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

from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt

from openPLM.apps.webdav.webdav_handler import WebDavHandler
from openPLM.apps.webdav.webdav_handler import WebDavHandlerException
from openPLM.apps.webdav.backends.openplm import OpenPLMBackend
from openPLM.apps.webdav.acl import WebDavPrivilegeException

from openPLM.plmapp.views.base import secure_required
from openPLM.plmapp.exceptions import ControllerError

logger = logging.getLogger("webdav")

@csrf_exempt
def not_found(request, *args, **kwargs):
    return HttpResponseNotFound("Not found")

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
        if user.profile.restricted:
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


if "django_digest" in settings.INSTALLED_APPS:
    # pip install "hg+https://bitbucket.org/scjody/django-digest" python_digest
    from django_digest import HttpDigestAuthenticator
    import python_digest

    from hashlib import md5

    def calc_ha2_rspauth(uri):
        return md5(":" + uri).hexdigest()

    def calc_hash(**parameters):
        hash_text = "%(ha1)s:%(nonce)s:%(nc)s:%(cnonce)s:auth:%(ha2)s" % parameters
        return md5(hash_text).hexdigest()

    def calc_rspauth(parameters):
        ha2_rspauth = calc_ha2_rspauth(parameters["uri"])
        return calc_hash(ha2=ha2_rspauth, **parameters)

    def _httpdigest(f):
        @csrf_exempt
        def wrapper(request, *args, **kwargs):
            authenticator = HttpDigestAuthenticator()
            if not authenticator.authenticate(request):
                return authenticator.build_challenge_response()

            response = f(request, *args, **kwargs)
            if hasattr(response, 'status_code') and response.status_code in [401, 403]:
                return authenticator.build_challenge_response()
            if 200 <= response.status_code < 300:
                digest = python_digest.parse_digest_credentials(
                    request.META['HTTP_AUTHORIZATION'])
                nc = "%08d" % digest.nc
                partial_digest = authenticator._account_storage.get_partial_digest(digest.username)
                parameters = {
                        "username": request.user.username,
                        "ha1": partial_digest,
                        "nonce": digest.nonce,
                        "cnonce": digest.cnonce,
                        "method":digest.algorithm,
                        "uri": digest.uri,
                        "nc": nc,
                        }
                rspauth = calc_rspauth(parameters)
                info = 'rspauth="%s",cnonce="%s",nc=%s,qop=%s' % (rspauth, digest.cnonce,
                        nc, digest.qop)
                response["Authentication-Info"] = info
            return response
        return wrapper
    openplm_webdav = _httpdigest(openplm_webdav)

