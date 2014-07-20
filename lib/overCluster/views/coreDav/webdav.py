"""
Copyright (c) 2014 Maciej Nabozny

This file is part of OverCluster project.

OverCluster is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import libvirt

from django.shortcuts import render
from django.http import HttpResponse, StreamingHttpResponse

from overCluster.models.core.image import Image
from overCluster.models.core.user import User
from overCluster.models.core.task import Task
from overCluster.utils import log

def call_options(request, token, type):
    response = HttpResponse()
    response['DAV'] = '1, 2, ordered-collections'
    response['Allow'] = 'OPTIONS, GET, HEAD, POST, PUT, DELETE, TRACE, COPY, MOVE, MKCOL, PROPFIND, PROPPATCH, LOCK, UNLOCK, ORDERPATCH'
    return response


def call_propfind(request, token, type):
    user = User.get_token(token)
    response = '''<?xml version="1.0" encoding="UTF-8"?>
        <d:multistatus xmlns:d="DAV:" xmlns:oc="http://owncloud.org/ns" xmlns:s="http://sabredav.org/ns">
           <d:response>
              <d:href>/storage/%(type)s/%(token)s/</d:href>
              <d:propstat>
                 <d:prop>
                    <oc:id>0000000252400eaba833a</oc:id>
                    <d:getlastmodified>Fri, 18 Jul 2014 11:55:47 GMT</d:getlastmodified>
                    <d:resourcetype>
                      <d:collection/>
                    </d:resourcetype>
                 </d:prop>
                 <d:status>HTTP/1.1 200 OK</d:status>
              </d:propstat>
              <d:propstat>
                 <d:prop>
                    <d:getcontentlength />
                    <x3:executable xmlns:x3="http://apache.org/dav/props/" />
                    <d:checked-in />
                    <d:checked-out />
                 </d:prop>
                 <d:status>HTTP/1.1 404 Not Found</d:status>
              </d:propstat>
           </d:response>''' % {
        'type': type,
        'token': token,
    }

    for image in Image.objects.filter(user=user).filter(type=Image.image_types[type]).all():
        log.debug(user.id, "CoreDav.propfind: Lisging image %d" % image.id)
        response += '''<d:response>
                         <d:href>%(image_id)d</d:href>
                         <d:propstat>
                            <d:prop>
                               <d:getcontentlength>%(image_size)d</d:getcontentlength>
                               <d:getlastmodified>%(modified)s</d:getlastmodified>
                               <d:name>%(name)s</d:name>
                               <d:resourcetype />
                            </d:prop>
                            <d:status>HTTP/1.1 200 OK</d:status>
                         </d:propstat>
                         <d:propstat>
                            <d:prop>
                               <x3:executable xmlns:x3="http://apache.org/dav/props/" />
                               <d:checked-in />
                               <d:checked-out />
                            </d:prop>
                            <d:status>HTTP/1.1 404 Not Found</d:status>
                         </d:propstat>
                      </d:response>''' % {
            'type': type,
            'token': token,
            'image_size': image.size,
            'image_id': image.id,
            'name': image.name,
            'modified': image.creation_date
        }

    response += '''</d:multistatus>'''
    response_object = HttpResponse(response)
    response_object.status_code = 207
    f = open('/tmp/log', 'a')
    f.write(response)
    f.close()
    return response_object


def call_delete(request, token, type, id):
    user = User.get_token(token)
    image = Image.objects.filter(user=user).get(pk=id)

    task = Task()
    task.type = Task.task_types['image']
    task.state = Task.states['not active']
    task.image = image
    task.setAllProps({'action': 'delete'})
    task.addAfterImage()

    response = HttpResponse()
    response.status_code = 200
    return response


def call_get(request, token, type, id):
    user = User.get_token(token)
    image = Image.objects.filter(user=user).get(pk=id)

    conn = libvirt.open('qemu:///system')
    storage = conn.storagePoolLookupByName(image.storage.name)
    if storage.info()[0] != libvirt.VIR_STORAGE_POOL_RUNNING:
        response = HttpResponse()
        response.status_code = 500
        response.reason_phrase = 'Storage unavailable'
        return response

    storage.refresh(0)
    volume = storage.storageVolLookupByName("%d_%d" % (image.user.id, image.id))
    stream = conn.newStream()

    try:
        def downloader(size):
            bytes = 0
            while bytes < size:
                chunk = stream.recv(1024*1024)
                if len(chunk) == 0:
                    break
                yield chunk
                log.debug(0, "Uploaded %d bytes from chunk starting at %d" % (len(chunk), bytes))
                bytes += len(chunk)


        volume.download(stream, 0, volume.info()[1])
        response = StreamingHttpResponse(downloader(volume.info()[1]), content_type="text/plain")
        conn.close()
        return response
    except Exception, e:
        log.error(0, str(e))
        response = HttpResponse()
        response.status_code = 500
        return response


def action(request, token, type, id):
    print "Action: " + request.method + " " + request.path
    try:
        if request.method == 'DELETE':
            return call_delete(request, token, type, id)
        elif request.method == 'GET':
            return call_get(request, token, type, id)
        elif request.method == 'PROPFIND':
            return call_propfind(request, token, type)
	else:
            return HttpResponse('webdav endpoint')
    except Exception, e:
        return HttpResponse(str(e))


def browse(request, token, type):
    print "Browse: " + request.path
    try:
        if request.method == 'OPTIONS':
            return call_options(request, token, type)
        elif request.method == 'PROPFIND':
            return call_propfind(request, token, type)
	else:
            return HttpResponse('webdav endpoint')
    except Exception, e:
        return HttpResponse(str(e))
