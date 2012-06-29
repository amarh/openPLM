"""
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
from openPLM.apps.webdav.util import get_class, ClassNotFoundException
from openPLM.apps.webdav.acl import WebDavAcl


class BackendException(Exception):
    pass


class BackendIOException(BackendException):
    pass


class BackendStorageException(BackendException):
    pass


class BackendResourceNotFoundException(BackendException):
    pass


class BackendLockException(BackendException):
    pass


class BackendLock(object):
    """
    Used for the WebDav backend locking mechanisms.
    """

    @classmethod
    def from_dict(cls, d):
        kwargs = {"exclusive": d.get("exclusive"),
                  "infinite": d.get("infinite"),
                  "timeout": d.get("timeout"),
                  "owner": d.get("owner"),
                  }
        return BackendLock(d.get("path"), d.get("token"), **kwargs)

    def __init__(self, path, token, **kwargs):
        if path is None:
            raise ValueError("no path specified")
        if token is None:
            raise ValueError("no token specified")
        self.path = path
        self.token = token
        self.exclusive = bool(kwargs.get("exclusive", True))
        self.infinite = bool(kwargs.get("infinite", True))
        self.owner = str(kwargs.get("owner", "") or "")
        try:
            self.timeout = int(kwargs.get("timeout", 0))
        except (TypeError, ValueError):
            raise ValueError("invalid timeout specified")

    def to_dict(self):
        return {"path":self.path,
                "token":self.token,
                "exclusive":self.exclusive,
                "infinite":self.infinite,
                "owner":self.owner,
                "timeout":self.timeout,
                }



class PropertySet(dict):

    def __init__(self, props = {}, status = "200 OK"):
        dict.__init__(self, props)
        self.status = status


class BackendItem(object):

    def __init__(self, name, is_collection = False, property_sets = []):
        self.name = name
        self.is_collection = is_collection        
        self.property_sets = [ps for ps in property_sets if ps]

    def add_properties(self, props = {}, status = "200 OK"):
        if props:
            self.property_sets.append(PropertySet(props, status))


class Backend(object):
    """
    Abstract files backend class.
    """
    LOCK_EX = 1
    LOCK_SH = 2

    @classmethod
    def validate_config(cls, config):
        """
        Validator for a specific backend. Config is a dictionary.
        Override to validate specific values in that dictionary.
        Raises django.core.exceptions.ValidationError if it fails.
        """
        return None

    @classmethod
    def get_category(cls):
        """
        Override. Return a string with the category name.
        """
        raise NotImplementedError()

    @classmethod
    def get_name(cls):
        """
        Override. Return proper human readable name as string.
        """
        raise NotImplementedError()

    def __init__(self, configuration, **kwargs):
        """
        All backends must take the configuration dictionary argument.
        If the configuration is bad, BackendConfigException is raised.
        """
        self.validate_config(configuration)
        self.configuration = configuration

    def get_acl(self, path):
        """
        Returns an empty WebDavAcl instance.
        """
        return WebDavAcl()

    def set_acl(self, path, acl):
        """
        Write WebDavAcl instance.
        """
        raise NotImplementedError()

    def dav_propfind(self, path, property_names = []):
        """
        The property_names argument can be used to specify which properties
        to return with the BackendItems. Empty list (default) means ALL
        properties.
        Return a list of BackendItem instances found in the specified path
        collection. Always include the resource specified in path.
        """
        raise NotImplementedError()

    def dav_set_properties(self, path, properties, token = None):
        """
        Set properties (dictionary) for resource.
        """
        raise NotImplementedError()

    def dav_remove_properties(self, path, property_names, token = None):
        """
        Remove properties (list of names) from resource.
        """
        raise NotImplementedError()

    def dav_mkcol(self, path, token = None):
        """
        Create a new collection for resource.
        """
        raise NotImplementedError()

    def dav_get(self, path):
        """
        Return readable file object.
        """
        raise NotImplementedError()

    def dav_head(self, path):
        """
        Not sure yet! FIXME!!!
        """
        raise NotImplementedError()

    def dav_delete(self, path, token = None):
        """
        Deletes the resource.
        """
        raise NotImplementedError()

    def dav_put(self, path, readable, token = None, estimated_size = 0):
        """
        Upload data using file object. (or any object with read method)
        """
        raise NotImplementedError()

    def dav_copy(self, from_path, to_path, token = None):
        """
        Copies a resource from one path to another.
        """
        raise NotImplementedError()

    def dav_move(self, from_path, to_path, token1 = None, token2 = None):
        """
        Movies a resource from one path to another.
        """
        raise NotImplementedError()

    def dav_lock(self, path, token = None, **kwargs):
        """
        Locks the resource, exclusive or shared, depth infinite or not.
        Must support the following keyword arguments:
        owner (str), exclusive (bool), infinite (bool) and timeout (int).
        Returns a BackendLock instance.
        """
        raise NotImplementedError()

    def dav_unlock(self, path, token, owner = None):
        """
        Unlocks the resource.
        """
        raise NotImplementedError()

    def dav_get_lock(self, path):
        """
        Returns a BackendLock instance.
        """
        raise NotImplementedError()
