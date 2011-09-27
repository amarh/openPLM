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
"""

import re

import openPLM.plmapp.models as models

_controller_rx = re.compile(r"(?P<type>\w+)Controller")

class MetaController(type):
    """
    Metaclass used to register a controller and get a controller associated
    to a type (see :meth:`get_controller`).

    See :ref:`how-to-add-a-controller` for more explanations.
    """
    #: dict<type_name(str) : Controller(like :class:`PLMObjectController`)>
    controllers_dict = {}

    def __new__(mcs, name, bases, attrs):
        cls = type.__new__(mcs, name, bases, attrs)
        if "MANAGED_TYPE" in attrs:
            managed = attrs["MANAGED_TYPE"].__name__
        else:
            m = _controller_rx.match(name)
            if m:
                managed = m.group("type")
            else:
                # the controller is not interresting
                return cls
        mcs.controllers_dict[managed] = cls
        return cls

    @classmethod
    def get_controller(cls, type_name):
        """
        Returns the controller (subclass of :class:`.PLMObjectController`) 
        associated to *type_name* (a string).

        For example, ``get_controller("Part")`` will return the class 
        :class:`.PartController`.
        """
        if type_name in cls.controllers_dict:
            return cls.controllers_dict[type_name]
        else:
            # get his model and return his parent controller
            if type_name == "PLMObject":
                # just a security to prevent an infinite recursion
                from openPLM.plmapp.controllers.plmobject import PLMObjectController
                return PLMObjectController
            else:
                model = models.get_all_plmobjects()[type_name]
                parents = [p for p in model.__bases__ 
                                if issubclass(p, models.PLMObject)]
                return cls.get_controller(parents[0].__name__)

#: shortcut for :meth:`MetaController.get_controller`
get_controller = MetaController.get_controller

