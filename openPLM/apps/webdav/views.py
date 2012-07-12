"""
openPLM.webdav application
Copyright 2012 LinObject

Modified version of webdav/views.py from:
    django-webdav is a small WebDAV implementation for Django.
    Copyright 2012 Peter Gebauer

This program is free software: you can redistribute it and/or modify
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
import logging
import base64

from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt

from openPLM.apps.webdav.webdav_handler import WebDavHandler
from openPLM.apps.webdav.webdav_handler import WebDavHandlerException
from openPLM.apps.webdav.backends.openplm import OpenPLMBackend
from openPLM.apps.webdav.acl import WebDavPrivilegeException

from openPLM.plmapp.base_views import secure_required
from openPLM.plmapp.exceptions import ControllerError

logger = logging.getLogger("webdav")

def basic_auth(request):
    """
    Authenticates the user with a basic http authentication
    and returns the user.
    Returns None if the user can not be authenticated.
    """

    if 'HTTP_AUTHORIZATION' in request.META:
        auth = request.META['HTTP_AUTHORIZATION'].split()
        if len(auth) == 2:
            # only basic auth is supported
            if auth[0].lower() == "basic":
                uname, passwd = base64.b64decode(auth[1]).split(':')
                user = authenticate(username=uname, password=passwd)
                if user is not None and user.is_active:
                    login(request, user)
                    request.user = user
                    return user
    return None

@csrf_exempt
@secure_required
def openplm_webdav(request, local_path):
    """
    View that handles all webdav requests.
    """
    if request.user.is_anonymous():
        user = basic_auth(request)
    else:
        user = request.user
    if user:
        if user.get_profile().restricted:
            return HttpResponseForbidden("403 Forbidden", None, 403, "text/plain")
        backend = OpenPLMBackend(user)
        handler = WebDavHandler(local_path, backend)
        try:
            return handler.handle_method(request)
        except WebDavHandlerException, wdhe:
            logger.error("handlers failed to handle request; %s"%wdhe)
            return HttpResponse("400 Bad Request", None, 400, "text/plain")
        except (WebDavPrivilegeException, ControllerError), wpe:
            logger.info("user '%s' failed privileges; %s"
                    %(request.user.username, wpe))
            return HttpResponse("403 Forbidden", None, 403, "text/plain")
        except NotImplementedError, nie:
            logger.warning("no implementation; %s"%nie)
            return HttpResponse("501 Not Implemented", None, 501, "text/plain")

    # failed authentication results in 401
    response = HttpResponse()
    response.status_code = 401
    response['WWW-Authenticate'] = 'Basic realm="openPLM-dav"'
    return response
