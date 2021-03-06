"""
Copyright (c) 2014 Maciej Nabozny

This file is part of CoreDav project.

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

from django.conf.urls import patterns, include, url
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^storage/(?P<type>[a-zA-Z]+)/(?P<token>[a-zA-Z0-9\-]+)/$', 'overCluster.views.coreDav.webdav.browse', name='browse'),
    url(r'^storage/(?P<type>[a-zA-Z]+)/(?P<token>[a-zA-Z0-9\-]+)/(?P<name>(?:(?!&#34;).)+)/?$', 'overCluster.views.coreDav.webdav.action', name='action'),
)
