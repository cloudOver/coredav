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


import os
import sys

sys.path.insert(0, '/usr/lib/cloudOver/')
sys.path.insert(0, '/etc/cloudOver/')

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "overCluster.settings_coredav")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
