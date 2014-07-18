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

from django.shortcuts import render
from django.http import HttpResponse

from overCluster.models.core.image import Image
from overCluster.models.core.user import User


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
              <d:href>/browse/%(type)s/%(token)s/</d:href>
              <d:propstat>
                 <d:prop>
                    <oc:id>0000000252400eaba833a</oc:id>
                    <d:getlastmodified>Fri, 18 Jul 2014 11:55:47 GMT</d:getlastmodified>
                    <d:resourcetype/>
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
        response += '''<d:response>
                         <d:href>/browse/%(type)s/%(token)s</d:href>
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
            'modified': image.creation_date
        }

    response += '''</d:multistatus>'''
    response_object = HttpResponse(response)
    response_object.status_code = 207
    return response_object


def browse(request, token, type):
    print request.method
    try:
        if request.method == 'OPTIONS':
            return call_options(request, token, type)
        if request.method == 'PROPFIND':
            return call_propfind(request, token, type)
    except Exception, e:
        print str(e)