"""
openPLM.webdav application
Copyright 2012 LinObject

Mostly inspired by webdav/backends/filesystem.py from:
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
import tempfile
import datetime
import time
from xml.etree.ElementTree import Element

from django.conf import settings
from django.core.files import File

from openPLM.apps.webdav.util import format_http_datetime, format_iso8601_datetime
from openPLM.apps.webdav.backends import Backend, BackendItem, PropertySet
from openPLM.apps.webdav.backends import BackendIOException
from openPLM.apps.webdav.backends import BackendResourceNotFoundException

from openPLM.plmapp.models import get_all_documents, Document, DocumentFile, docfs
from openPLM.plmapp.views.base import get_obj


logger = logging.getLogger("webdav")

def rfc3339_date(date):
    if not date:
        return ''
    if not isinstance(date, datetime.date):
        date = datetime.date.fromtimestamp(date)
    date = date + datetime.timedelta(seconds=-time.timezone)
    if time.daylight:
        date += datetime.timedelta(seconds=time.altzone)
    return date.strftime('%Y-%m-%dT%H:%M:%SZ')


def safe_copyfileobj(fsrc, fdst, length=16*1024, size=0):
    """
    A version of shutil.copyfileobj that will not read more than 'size' bytes.
    This makes it safe from clients sending more than CONTENT_LENGTH bytes of
    data in the body.
    """
    # from  django/core/handlers/wsgi.py
    if not size:
        return
    while size > 0:
        buf = fsrc.read(min(length, size))
        if not buf:
            break
        fdst.write(buf)
        size -= len(buf)

class OpenPLMBackend(Backend):
    """
    Implements a backend to browse/edit documents/files stored by openPLM.
    """

    def __init__(self, user):
        self.user = user

    def get_doc(self, path):
        p = path.strip("/").split("/")
        if len(p) >= 3:
            try:
                return get_obj(p[0], p[1], p[2], self.user), p[3:]
            except:
                raise BackendResourceNotFoundException(path)
        return None, p

    def dav_propfind(self, path, property_list, depth="1"):
        ret = []
        ctrl, p = self.get_doc(path)
        now = datetime.datetime.utcnow()
        self.now = now

        files = [ {"size": 4096, "locked" : False, "locker" : None,
                  "filename" : "", "is_dir" : True, "ctime" : now,  "mtime" : now,} ]
        if ctrl is None and depth != "0":
            if not p or not p[0]:
                filenames = sorted(get_all_documents().keys())
            elif len(p) == 1:
                if p[0] not in get_all_documents():
                    raise BackendResourceNotFoundException(path)
                qs = Document.objects.filter(type=p[0]).values_list("reference", flat=True)
                filenames = set(qs)
            elif len(p) == 2:
                t, ref = p
                qs = Document.objects.filter(type=t, reference=ref).values_list("revision", flat=True)
                filenames = set(qs)
                if not filenames:
                    # in that case, it is not possible to have an empty folder
                    raise BackendResourceNotFoundException(path)
            for name in filenames:
                files.append({"size": 4096, "locked" : False, "locker" : None,
                    "filename" : name, "is_dir" : True, "ctime" : now,  "mtime" : now,})
        elif ctrl is not None:
            ctrl.check_readable(raise_=True)
            if p:
                if len(p) != 1:
                    raise BackendResourceNotFoundException(path)
                try:
                    df = ctrl.files.get(filename=p[0])
                except DocumentFile.DoesNotExist:
                    raise BackendResourceNotFoundException(path)
                else:
                    files = [ {"size": df.size, "locked" : df.locked, "locker" : df.locker,
                    "filename" : "", "is_dir" : False, "ctime" : now,  "mtime" : now,}]

            elif depth != "0":
                for f in ctrl.files.values():
                    f["is_dir"] = False
                    try:
                        st = os.stat(docfs.path(f["file"]))
                        f["ctime"] = datetime.datetime.fromtimestamp(st.st_ctime)
                        f["mtime"] = datetime.datetime.fromtimestamp(st.st_mtime)
                    except OSError:
                        f["ctime"] = f["mtime"] = now
                    files.append(f)

        for f in files:
            props_ok = {}
            props_not_found = {}
            for prop in property_list:
                if prop == "{DAV:}getcontentlength":
                    if not f["is_dir"]:
                        props_ok["{DAV:}getcontentlength"] = f["size"]
                elif prop == "{DAV:}getlastmodified":
                    props_ok["{DAV:}getlastmodified"] = format_http_datetime(f["mtime"])
                elif prop == "{DAV:}creationdate":
                    props_ok["{DAV:}creationdate"] = rfc3339_date(f["ctime"])
                elif prop == "{DAV:}resourcetype":
                    if f["is_dir"]:
                        props_ok["{DAV:}resourcetype"] = Element("{DAV:}collection")
                    else:
                        props_ok["{DAV:}resourcetype"] = None
                elif prop == "{DAV:}checked-in":
                    pass
                elif prop == "{DAV:}checked-out":
                    pass
                elif prop == "{http://apache.org/dav/props/}executable":
                    props_ok["{http://apache.org/dav/props/}executable"] = False
                elif prop == "{DAV:}supportedlock":
                    lockentries = [Element("{DAV:}lockentry"),
                                   Element("{DAV:}lockentry")]
                    scope = Element("{DAV:}lockscope")
                    scope.append(Element("{DAV:}exclusive"))
                    lockentries[0].append(scope)
                    type_ = Element("{DAV:}locktype")
                    type_.append(Element("{DAV:}write"))
                    lockentries[0].append(type_)
                    scope = Element("{DAV:}lockscope")
                    scope.append(Element("{DAV:}shared"))
                    lockentries[1].append(scope)
                    type_ = Element("{DAV:}locktype")
                    type_.append(Element("{DAV:}write"))
                    lockentries[1].append(type_)
                    props_ok["{DAV:}supportedlock"] = lockentries
                elif prop == "{DAV:}displayname":
                    pass
                elif prop == "{DAV:}ishidden":
                    props_ok[prop] = False
                elif prop == "{DAV:}getcontenttype":
                    if f["is_dir"]:
                        props_ok[prop] = "httpd/unix-directory"
                else:
                    logger.debug("unsupported property '%s'"%prop)
                    props_not_found[prop] = None

            f = BackendItem(
                f["filename"],
                f["is_dir"],
                [PropertySet(props_ok),
                 PropertySet(props_not_found, "404 Not Found")]
                )
            ret.append(f)
        logger.debug("returned contents of directory '%s'"%p)
        return ret

    def dav_set_properties(self, path, properties):
        # TODO: really implement this method
        # dummy implementation required by the Windows client
        return []

    def dav_remove_properties(self, path, property_names):
        raise NotImplementedError()

    def dav_mkcol(self, path):
        raise NotImplementedError()

    def dav_get(self, path):
        d, p = self.get_doc(path)
        if len(p) != 1:
            raise BackendResourceNotFoundException(path)
        d.check_readable()
        df = d.files.get(filename=p[0], deprecated=False)
        try:
            f, size = d.get_content_and_size(df)
            logger.debug("opened file '%s' for reading"%p)
            return f
        except IOError, ioe:
            raise BackendIOException(ioe)

    def dav_head(self, path):
        ctrl, p = self.get_doc(path)
        if ctrl:
            ctrl.check_readable(raise_=True)
            if p and not ctrl.files.filter(filename="/".join(p)).exists():
                raise BackendResourceNotFoundException(path)

    def dav_delete(self, path, token = None):
        d, p = self.get_doc(path)
        df = d.files.get(filename=p[0], deprecated=False)
        if d:
            d.delete_file(df)
            return
        raise BackendIOException("Can not delete a directory")

    def dav_put(self, path, readable, token = None, estimated_size = 0):
        d, p = self.get_doc(path)
        if d and p:
            if len(p) > 1:
                raise BackendIOException()
            tmpdir = settings.FILE_UPLOAD_TEMP_DIR
            with tempfile.NamedTemporaryFile(mode="r+w", dir=tmpdir) as f:
                logger.debug("opened file '%s' for writing"%p)
                data = readable.read()
                while data:
                    f.write(data)
                    data = readable.read()
                f.flush()
                f.seek(0)
                f2 = File(open(f.name, "rb"), p[0])
                if d.files.filter(filename=p[0]).exists():
                    d.checkin(d.files.get(filename=p[0]), f2)
                else:
                    d.add_file(f2)
                return

        raise BackendIOException("Can not add a file")

    def dav_copy(self, path1, path2, token = None):
        raise NotImplementedError()

    def dav_move(self, path1, path2, token1 = None, token2 = None):
        raise NotImplementedError()

    def dav_lock(self, path, token = None, **kwargs):
        raise NotImplementedError()

    def dav_unlock(self, path, token, owner = None):
        raise NotImplementedError()

    def dav_get_lock(self, path):
        raise NotImplementedError()


