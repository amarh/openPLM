"""
openPLM.webdav application
Copyright 2012 LinObject

Modified version of webdav/webdav_handler.py from:
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
import os
import logging
from urlparse import urlparse

from django.conf import settings
from django.http import HttpResponse, StreamingHttpResponse
from django.core.exceptions import ImproperlyConfigured

from openPLM.apps.webdav.backends import BackendIOException
from openPLM.apps.webdav.backends import BackendResourceNotFoundException
from openPLM.apps.webdav.backends import BackendStorageException
from openPLM.apps.webdav.backends import BackendLockException
from openPLM.apps.webdav.backends import BackendItem, PropertySet
from openPLM.apps.webdav.util import get_propfind_properties_from_xml
from openPLM.apps.webdav.util import get_multistatus_response_xml
from openPLM.apps.webdav.util import get_lock_response_xml
from openPLM.apps.webdav.util import format_http_datetime


logger = logging.getLogger("webdav")


class WebDavHandlerException(Exception):
    pass


class WebDavHandler(object):

    def __init__(self, resource_path, backend, **kwargs):
        self.resource_path = resource_path
        if not backend:
            raise ImproperlyConfigured("no backend!")
        self.backend = backend

    def get_final_path_part(self, localpath):
        return self.resource_path
        if not localpath:
            return None
        if localpath == ".":
            return ""
        if localpath.startswith(self.resource_path):
            return os.path.normpath(localpath[len(self.resource_path):])
        return None

    def get_supported_methods(self):
        return ["OPTIONS", "PROPFIND", "PROPPATCH", "MKCOL", "GET", "HEAD",
                "DELETE", "PUT", "COPY", "MOVE", "LOCK", "UNLOCK"]

    def parse_if_header(self, request):
        ret = []
        http_if = request.META.get("HTTP_IF")
        if http_if:
            parsing_path = False
            parsing_token = False
            path = ""
            token = ""
            for index, char in enumerate(http_if):
                if parsing_path:
                    if char == '>':
                        parsing_path = False
                        continue
                    path += char
                elif parsing_token:
                    if char == ')':
                        parsing_token = False
                        continue
                    elif char == '<' or char == '>':
                        continue
                    token += char
                elif char == '<':
                    parsing_path = True
                elif char == '(':
                    parsing_token = True
            if path and token:
                ret.append((path, token))
        return ret

    def get_matching_token(self, request, path):
        token = request.META.get("HTTP_LOCK_TOKEN", "")
        if token:
            return token
        parsed = self.parse_if_header(request)
        for lpath, token in parsed:
            ppath = urlparse(lpath)
            testpath = self.get_final_path_part(ppath.path)
            if testpath and testpath == path:
                return token
        return ""

    def handle_method(self, request):
        try:
            if request.method == "OPTIONS":
                return self.handle_options(request)
            elif request.method == "PROPFIND":
                return self.handle_propfind(request)
            elif request.method == "PROPPATCH":
                return self.handle_proppatch(request)
            elif request.method == "MKCOL":
                return self.handle_mkcol(request)
            elif request.method == "GET":
                return self.handle_get(request)
            elif request.method == "HEAD":
                return self.handle_head(request)
            elif request.method == "DELETE":
                return self.handle_delete(request)
            elif request.method == "PUT":
                return self.handle_put(request)
            elif request.method == "COPY":
                return self.handle_copy(request)
            elif request.method == "MOVE":
                return self.handle_move(request)
            elif request.method == "LOCK":
                return self.handle_lock(request)
            elif request.method == "UNLOCK":
                return self.handle_unlock(request)
        except BackendIOException, beioe:
            logger.warning(beioe)
            raise WebDavHandlerException(beioe)
        except BackendResourceNotFoundException, brnfe:
            logger.debug(brnfe)
            return HttpResponse("404 Not Found", None, 404, "text/plain")
        except BackendStorageException, brnfe:
            logger.debug(brnfe)
            return HttpResponse("507 Insufficient Storage", None, 507, "text/plain")
        except BackendLockException, ble:
            logger.debug(ble)
            return HttpResponse("423 Locked", None, 423, "text/plain")
        except NotImplementedError:
            raise NotImplementedError("backend method '%s' not implemented"%request.method)
        raise NotImplementedError("invalid method '%s' for handler class '%s'"%(request.method, type(self).__name__))

    def handle_options(self, request):
        res = HttpResponse('', None, 200, "text/plain")
        res["Allow"] = ", ".join(self.get_supported_methods())
        res["DAV"] = "1, 2"
        return res

    def get_200_response(self):
        response = HttpResponse("200 OK", None, 200, "text/plain")
        response["Content-Length"] = 6
        return response

    def handle_propfind(self, request):
        path = self.get_final_path_part(request.path)
        props = get_propfind_properties_from_xml(request.body)
        depth = request.META.get("HTTP_DEPTH", "1")
        items = self.backend.dav_propfind(path, props, depth)
        s = get_multistatus_response_xml(request.path, items)
        response = HttpResponse(s, None, 207, "text/xml; charset=utf-8")
        response["Content-Length"] = len(s)
        response["DAV"] = "1, 2"
        response["Depth"] = depth
        return response

    def handle_proppatch(self, request):
        path = self.get_final_path_part(request.path)
        props = get_propfind_properties_from_xml(request.body)
        depth = request.META.get("HTTP_DEPTH", "1")
        items = self.backend.dav_set_properties(path, props)
        s = get_multistatus_response_xml(request.path, items)
        response = HttpResponse(s, None, 207, "text/xml; charset=utf-8")
        response["Content-Length"] = len(s)
        response["DAV"] = "1, 2"
        response["Depth"] = depth
        return response

    def handle_mkcol(self, request):
        path = self.get_final_path_part(request.path)
        self.backend.dav_mkcol(path)
        response = HttpResponse("200 OK", None, 200, "text/plain")
        return response

    def handle_get(self, request):
        path = self.get_final_path_part(request.path)
        f = self.backend.dav_get(path)
        response = StreamingHttpResponse(f, None, 200, "text/plain")
        return response

    def handle_head(self, request):
        path = self.get_final_path_part(request.path)
        self.backend.dav_head(path)
        return self.get_200_response()

    def handle_delete(self, request):
        path = self.get_final_path_part(request.path)
        token = self.get_matching_token(request, path)
        self.backend.dav_delete(path, token)
        return self.get_200_response()

    def handle_put(self, request):
        path = self.get_final_path_part(request.path)
        token = self.get_matching_token(request, path)
        self.backend.dav_put(path, request, token)
        return self.get_200_response()

    def handle_copy(self, request):
        path1 = self.get_final_path_part(request.path)
        parsed = urlparse(request.META.get("HTTP_DESTINATION"))
        path2 = self.get_final_path_part(parsed.path)
        token = self.get_matching_token(request, path2)
        if not path2:
            raise WebDavHandlerException("missing destination header for copy")
        self.backend.dav_copy(path1, path2, token)
        response = HttpResponse("201 OK", None, 201, "text/plain")
        return response

    def handle_move(self, request):
        path1 = self.get_final_path_part(request.path)
        token1 = self.get_matching_token(request, path1)
        parsed = urlparse(request.META.get("HTTP_DESTINATION"))
        path2 = self.get_final_path_part(parsed.path)
        token2 = self.get_matching_token(request, path2)
        if not path2:
            raise WebDavHandlerException("missing destination header for move")
        self.backend.dav_move(path1, path2, token1, token2)
        response = HttpResponse("201 OK", None, 201, "text/plain")
        return response

    def handle_lock(self, request):
        path = self.get_final_path_part(request.path)
        token = request.META.get("HTTP_LOCK_TOKEN")
        if not token:
            items = self.parse_if_header(request)
            if items:
                parsed = urlparse(items[0][0])
                path = self.get_final_path_part(parsed.path)
                token = items[0][1]
        lock = self.backend.dav_lock(path,
                                     token,
                                     owner=request.user.username,
                                     exclusive=True,
                                     infinite=True,
                                     timeout=0,
                                     )
        if lock:
            s = get_lock_response_xml(lock.to_dict())
            response = HttpResponse(s, None, 200, "text/xml; charset=utf-8")
            response["Lock-Token"] = lock.token
        else:
            response = HttpResponse("412 Precondition Failed", None, 412,
                                    "text/plain")
        return response

    def handle_unlock(self, request):
        path = self.get_final_path_part(request.path)
        token = request.META.get("HTTP_LOCK_TOKEN")
        if token.startswith("<"):
            token = token[1:]
        if token.endswith(">"):
            token = token[:-1]
        self.backend.dav_unlock(path, token, request.user.username)
        response = HttpResponse("204 No Content", None, 204, "text/plain")
        return response


