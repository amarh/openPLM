############################################################################
# openPLM - open source PLM
# Copyright 2010 Philippe Joulaud, Pierre Cosquer
# 
# This file is part of openPLM.
#
#    openPLM is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    openPLM is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact :
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pierre.cosquer@insa-rennes.fr
################################################################################

"""
This module contains a class called :class:`GroupController` which
provides a controller for :class:`~django.contrib.auth.models.Group`.
This class is similar to :class:`.PLMObjectController` but some methods
from :class:`.PLMObjectController` are not defined.
"""


import openPLM.plmapp.models as models
from openPLM.plmapp.controllers.base import Controller

class GroupController(Controller):
    u"""
    Object used to manage a :class:`~django.contrib.auth.models.Group` and store his 
    modification in an history
    
    :attributes:
        .. attribute:: object

            The :class:`~django.contrib.auth.models.Group` managed by the controller

    :param obj: managed object
    :type obj: an instance of :class:`~django.contrib.auth.models.Group`
    :param user: user who modify *obj*
    :type user: :class:`~django.contrib.auth.models.Group` 

    .. note::
        This class does not inherit from :class:`.PLMObjectController`.

    """

    HISTORY = models.GroupHistory

    def __init__(self, obj, user):
        super(GroupController, self).__init__(obj, user)
        self.group_info = models.GroupInfo.objects.get(group=obj)
    
    def __setattr__(self, attr, value):
        # we override this method to make it to modify *object* directly
        # (or its profile)
        # if we modify *object*, we records the modification in **_histo*
        if hasattr(self, "object"):
            obj = object.__getattribute__(self, "object")
        else:
            obj = None
        if hasattr(self, "group_info"):
            gi = object.__getattribute__(self, "group_info")
        else:
            gi = None
        if obj and (hasattr(obj, attr) or hasattr(gi, attr)) and \
           not attr in self.__dict__:
            obj2 = obj if hasattr(obj, attr) else gi
            old_value = getattr(obj2, attr)
            setattr(obj2, attr, value)
            # since x.verbose_name is a proxy methods, we need to get a real
            # unicode object (with capitalize)
            field = obj2._meta.get_field(attr).verbose_name.capitalize()
            if old_value != value:
                message = "%(field)s : changes from '%(old)s' to '%(new)s'" % \
                        {"field" : field, "old" : old_value, "new" : value}
                self._histo += message + "\n"
        else:
            super(GroupController, self).__setattr__(attr, value)

    def __getattr__(self, attr):
        # we override this method to get attributes from *object* directly
        # (or its profile)
        obj = object.__getattribute__(self, "object")
        gi = object.__getattribute__(self, "group_info")
        if hasattr(self, "object") and hasattr(obj, attr) and \
           not attr in self.__dict__:
            return getattr(obj, attr)
        elif hasattr(gi, attr) and not attr in self.__dict__:
            return getattr(gi, attr)
        else:
            return object.__getattribute__(self, attr)

    def save(self, with_history=True):
        u"""
        Saves :attr:`object` and records its history in the database.
        If *with_history* is False, the history is not recorded.
        """
        self.group_info.save()
        super(GroupController, self).save(with_history)

    def has_permission(self, role):
        if role == models.ROLE_OWNER:
            return self.owner == self._user
        return False
