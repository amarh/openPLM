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
#    along with openPLM.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact :
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pcosquer@linobject.com
################################################################################

"""
Introduction
=============

This module contains utilities to manage a :class:`.PLMObject`.
It provides a new class, :class:`.PLMObjectController`, which can be used to
modify its attributes, promote/demote/revise it...

All modifications are recorded in a history.

How to use this module
======================

The controller for a ``PLMObject`` is :class:`PLMObjectController`.
All subclasses of ``PLMObject`` may have their own controller to add
functionalities or redefined default behaviors.

To get a suitable controller for a ``PLMObject`` instances use
:func:`~plmapp.controllers.base.get_controller`.
For example, `get_controller('Part')` returns :class:`.PartController`.

If you have a ``PLMObject`` and an User, you can instanciate a controller.
For example::

    >>> # obj is a PLMObject and user an User
    >>> controller_cls = get_controller(obj.type)
    >>> controller = controller_cls(obj, user)

Then you can modify/access the attributes of the ``PLMObject`` and save the
modifications:

    >>> controller.name = "New Name"
    >>> "type" in controller.attributes
    True
    >>> controller.owner = user
    >>> # as with django models, you should call *save* to register modifications
    >>> controller.save()

You can also promote/demote the ``PLMObject``:

    >>> controller.state.name
    'draft'
    >>> controller.promote()
    >>> controller.state.name
    'official'
    >>> controller.demote()
    >>> controller.state.name
    'draft'

There are also two classmethods which can help to create a new ``PLMobject``:

    * :meth:`~PLMObjectController.create`
    * :meth:`~PLMObjectController.create_from_form`

This two methods return an instance of :class:`PLMObjectController` (or one of
its subclasses).

Moreover, the method :meth:`~PLMObjectController.create_from_form` can be used
to update informations from a form created with
:func:`plmapp.forms.get_modification_form`.


.. _how-to-add-a-controller:

How to add a controller
=======================

If you add a new model which inherits from :class:`.PLMObject`
or one of its subclasses, you may want to add your own controller.

You just have to declare a class which inherits (directly or not) from
:class:`.PLMObjectController`. To associate this class with your models, there
are two possibilities:

    * if your class has an attribute *MANAGED_TYPE*, its value (a class)
      will be used.
      For example::

          class MyController(PLMObjectController):
              MANAGED_TYPE = MyPart
              ...

      *MyController* will be associated to *MyPart* and
      ``get_controller("MyPart")`` will return *MyController*.

    * if *MANAGED_TYPE* is not defined, the name class will be used: for
      example, *MyPartController* will be associated to *MyPart*. The rule
      is simple, it is just the name of the model followed by "Controller".
      The model may not be defined when the controller is written.

If a controller exploits none of theses possibilities, it will still
work but it will not be associated to a type and will not be used by existing
views.

.. note::

    This association is possible without any registration because
    :class:`.PLMObjectController` metaclass is :class:`.MetaController`.

If your controller has its own attributes, you must redefine the variable
``__slots__`` and add its attributes::

    class MyController(PLMObjectController):

        __slots__ = PLMObjectController.__slots__ + ("my_attr", )

        def __init__(self, object, user):
            super(MyController, self).__init__(object, user)
            self.my_attr = "value"

By default, a controller inherits its ``__slots__`` attribute from its parent
(this is set by :class:`.MetaController`).


Classes and functions
=====================

This module defines several classes, here is a summary:

    * metaclasses:
        - :class:`.MetaController`
    * :class:`~collections.namedtuple` :
        - :class:`.Child`
        - :class:`.Parent`
    * controllers:

        =================== ===============================
              Type              Controller
        =================== ===============================
        :class:`.PLMObject` :class:`.PLMObjectController`
        :class:`.Part`      :class:`.PartController`
        :class:`.Document`  :class:`.DocumentController`
        :class:`User`       :class:`.UserController`
        :class:`.GroupInfo` :class:`.GroupController`
        =================== ===============================

    * functions:
        :func:`~plmapp.controllers.base.get_controller`

"""
from openPLM.plmapp.controllers.base import MetaController, get_controller
from openPLM.plmapp.controllers.plmobject import PLMObjectController
from openPLM.plmapp.controllers.part import PartController
from openPLM.plmapp.controllers.document import DocumentController

from openPLM.plmapp.controllers.user import UserController
from openPLM.plmapp.controllers.group import GroupController

MetaController.controllers_dict["GroupInfo"] = GroupController


