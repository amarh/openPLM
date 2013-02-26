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
import json
from django.core.serializers.json import DjangoJSONEncoder


class WebDavPrivilegeException(Exception):
    pass


class WebDavAcl(object):
    PRIVILEGES = ["write",
                  "write-property",
                  "write-content",
                  "unlock",
                  "read-acl",
                  "write-acl",
                  "read-current-user-privilege-set",
                  "bind",
                  "unbind",
                  "all"]

    def __init__(self, user_dict = {}, group_dict = {}):
        self.user_dict = user_dict
        self.group_dict = group_dict

    @classmethod
    def from_json(cls, value):
        try:
            value = json.loads(str(value))
        except ValueError:
            return None
        user_dict = value.get("users", {})
        group_dict = value.get("groups", {})
        return cls(user_dict, group_dict)

    def to_json(self):
        value = {"users": self.user_dict,
                 "groups": self.group_dict}
        return json.dumps(value, cls=DjangoJSONEncoder)

    def get_privileges(self, djangouser):
        """
        Returns a list of strings containing the names of the privileges
        this user or any of the user's groups has.
        """
        ret = []
        ret += self.user_dict.get(djangouser.username, [])
        for group in djangouser.groups.all():
            ret += self.group_dict.get(group.name, [])
        unique = {}
        for r in ret:
            unique[r] = None
        keys = unique.keys()
        keys.sort()
        return keys

    def get_privileges_for_user(self, djangouser):
        """
        Return a list of privileges for a user.
        """
        return self.user_dict.get(djangouser.username, [])

    def set_privileges_for_user(self, djangouser, privs):
        """
        Set a list of privileges for the user.
        """
        self.user_dict[djangouser.username] = privs

    def get_privileges_for_group(self, group):
        """
        Return a list of privileges for a group.
        """
        return self.group_dict.get(group.name, [])

    def set_privileges_for_group(self, group, privs):
        """
        Set a list of privileges for the group.
        """
        self.group_dict[group.name] = privs

    def has_privileges(self, djangouser, *privs):
        """
        Tests whether or not the user has the specified privs.
        """
        has_privs = self.get_privileges(djangouser)
        if "all" in has_privs:
            return True
        for priv in privs:
            if priv in has_privs:
                return True
        return False

    def test_privileges(self, djangouser, *privs):
        if not self.has_privileges(djangouser, *privs):
            raise WebDavPrivilegeException(", ".join(privs))




