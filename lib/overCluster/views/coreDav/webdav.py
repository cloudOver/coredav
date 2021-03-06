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
import urllib
import os
from django.http import HttpResponse, StreamingHttpResponse

from overCluster.models.core.image import Image
from overCluster.models.core.user import User
from overCluster.models.core.task import Task
from overCluster.models.core.token import Token
from overCluster.utils.decorators import register
from overCluster.utils.exception import CMException
from overCluster import settings


@register(auth='password')
def enable(context, token_id, enable):
    """ Enable or disable webdav for given token

    :param token_id: Id of token, which should be available as webdav resource
    :param enable: Should be this token enabled (True) or disabled (False)
    """
    token = Token.objects.filter(user=context.user).get(id=token_id)
    token.set_prop('webdav_enabled', enable)
    token.save()


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

    for image in Image.objects.filter(user=user).filter(type=type).all():
        if image.state != 'ok':
            continue
        response += '''<d:response>
                         <d:href>%(image_name)s</d:href>
                         <d:propstat>
                            <d:prop>
                               <d:getcontentlength>%(image_size)d</d:getcontentlength>
                               <d:getlastmodified>%(modified)s</d:getlastmodified>
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
            'image_name': urllib.quote_plus(image.name),
            #'image_name': image.name,
            'modified': image.creation_date
        }

    response += '''</d:multistatus>'''
    response_object = HttpResponse(response)
    response_object.status_code = 207
    return response_object


def call_delete(request, token, type, name):
    user = User.get_token(token)

    images = Image.objects.filter(user=user).filter(state='ok').all()
    image = None
    for i in images:
        if name == urllib.quote_plus(i.name):
            image = i

    if image == None:
        response = HttpResponse()
        response.status_code = 404
        response.reason_phrase = "Not found"
        return response

    task = Task()
    task.type = 'image'
    task.action = 'delete'
    task.state = 'not active'
    task.image = image
    task.addAfterImage()

    response = HttpResponse()
    response.status_code = 200
    return response


def call_put(request, token, type, name):
    user = User.get_token(token)
    user.check_storage(len(request.body))

    filename = os.path.join(settings.UPLOAD_DIR, 'oc_upload_%s' % user.id)
    if os.path.exists(filename):
        response = HttpResponse()
        response.status_code = 403
        response.reason_phrase = "You have upload active"
        return response

    if len(request.body) > settings.MAX_UPLOAD_CHUNK_SIZE:
        response = HttpResponse()
        response.status_code = 403
        response.reason_phrase = "File too large (max. size %d)" % settings.MAX_UPLOAD_CHUNK_SIZE
        return response

    f = open(filename, 'w')
    f.write(request.body)
    f.close()

    image = Image.create(user, name, "", 1, type, 'virtio', 'private', 'raw')
    image.save()

    task = Task()
    task.type = 'image'
    task.action = 'create'
    task.state = 'not active'
    task.image = image
    task.storage = image.storage
    task.addAfterStorage()

    task = Task()
    task.type = 'image'
    task.action = 'upload_data'
    task.state = 'not active'
    task.image = image
    task.set_all_props({'offset': 0,
                        'size': len(request.body),
                        'filename': filename})
    task.addAfterImage()

    return HttpResponse()


def call_get(request, token, type, name):
    user = User.get_token(token)

    images = Image.objects.filter(user=user).filter(state='ok').all()
    image = None
    for i in images:
        if name == urllib.quote_plus(i.name):
            image = i

    if image == None:
        response = HttpResponse()
        response.status_code = 404
        response.reason_phrase = "Not found"
        return response

    conn = libvirt.open('qemu:///system')
    storage = conn.storagePoolLookupByName(image.storage.name)
    if storage.info()[0] != libvirt.VIR_STORAGE_POOL_RUNNING:
        response = HttpResponse()
        response.status_code = 500
        response.reason_phrase = 'Storage unavailable'
        return response

    storage.refresh(0)
    volume = storage.storageVolLookupByName(image.libvirt_name)
    stream = conn.newStream(0)

    try:
        def downloader(size):
            bytes = 0
            while bytes < size:
                chunk = stream.recv(1024*1024)
                if len(chunk) == 0:
                    break
                yield chunk
                bytes += len(chunk)


        volume.download(stream, 0, volume.info()[1], 0)
        response = StreamingHttpResponse(downloader(volume.info()[1]), content_type="text/plain")
        conn.close()
        return response
    except Exception, e:
        response = HttpResponse()
        response.status_code = 500
        return response


def call_move(request, token, type, name):
    user = User.get_token(token)

    images = Image.objects.filter(user=user).filter(state='ok').all()
    image = None
    for i in images:
        if name == urllib.quote_plus(i.name):
            image = i

    if image == None:
        response = HttpResponse()
        response.status_code = 404
        response.reason_phrase = "Not found"
        return response

    image.name = os.path.basename(request.META['HTTP_DESTINATION'])
    image.save()
    return HttpResponse()


def action(request, token, type, name):
    user = User.get_token(token)
    token = Token.objects.filter(user=user).filter(token=token).get()
    if not token.get_prop('webdav_enabled', False):
        response = HttpResponse()
        response.status_code = 403
        response.reason_phrase = 'This token is not allowed for webdav'
        return response


    try:
        if request.method == 'DELETE':
            return call_delete(request, token, type, name)
        elif request.method == 'GET':
            return call_get(request, token, type, name)
        elif request.method == 'PUT':
            return call_put(request, token, type, name)
        elif request.method == 'PROPFIND':
            return call_propfind(request, token, type)
        elif request.method == 'MOVE':
            return call_move(request, token, type, name)
        else:
            return HttpResponse('webdav endpoint')
    except Exception, e:
        return HttpResponse(str(e))


def browse(request, token, type):
    user = User.get_token(token)
    token = Token.objects.filter(user=user).filter(token=token).get()
    if not token.get_prop('webdav_enabled', False):
        response = HttpResponse()
        response.status_code = 403
        response.reason_phrase = 'This token is not allowed for webdav'
        return response

    try:
        if request.method == 'OPTIONS':
            return call_options(request, token, type)
        elif request.method == 'PROPFIND':
            return call_propfind(request, token, type)
        else:
            return HttpResponse('webdav endpoint')
    except Exception, e:
        return HttpResponse(str(e))
