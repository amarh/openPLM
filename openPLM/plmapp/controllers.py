"""
Introduction
=============

This module contains utilities to manage a :class:`~openPLM.plmapp.models.PLMObject`.
It provides a new class, :class:`PLMObjectController`, which can be used to
modify its attributes, promote/demote/revise it...

All modifications are recorded in an history.

How to use this module
======================

The controller for a ``PLMObject`` is :class:`PLMObjectController`.
All subclasses of ``PLMObject`` may have their own controller to add
functionalities or redefined default behaviors.

To get a suitable controller for a ``PLMObject`` instances use :func:`get_controller`.
For example, `get_controller('Part')` returns :class:`PartController`.

If you have a ``PLMObject`` and an User, you can instanciate a controller.
For example::

    >>> # obj is a PLMObject and user an User
    >>> controller_cls = get_controller(obj.type)
    >>> controller = controller_cls(obj, user)

Then you can modify/access the attributes of the PLMObject and save the
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
    

How to add a controller
=======================

If you add a new model which inherits from :class:`~openPLM.plmapp.models.PLMObject`
or one of its subclasses, you may want to add your own controller.

You just have to declare a class which inherits (directly or not) from 
:class:`PLMObjectController`. To associate this class with your models, there
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
work but it will not be associated to a type.

.. note::

    This association is possible without any registration because 
    :class:`PLMObjectController` metaclass is :class:`MetaController`.

Classes and functions
=====================

This module defines several classes, here is a summary:

    * exceptions:
        - :exc:`RevisionError`
    * metaclasses:
        - :class:`MetaController`
    * :class:`~collections.namedtuple` :
        - :class:`Child`
        - :class:`Parent`
    * controllers:

        ========================================= ============================
                          Type                             Controller
        ========================================= ============================
        :class:`~openPLM.plmapp.models.PLMObject` :class:`PLMObjectController`
        :class:`~openPLM.plmapp.models.Part`      :class:`PartController`
        :class:`~openPLM.plmapp.models.Document`  :class:`DocumentController`
        ========================================= ============================
    
    * functions:
        :func:`get_controller`

"""

import re
from datetime import datetime
from collections import namedtuple

from django.core.exceptions import ObjectDoesNotExist

try:
    import openPLM.plmapp.models as models
except (ImportError, AttributeError):
    import plmapp.models as models

_controller_rx = re.compile(r"(?P<type>\w+)Controller")

class RevisionError(StandardError):
    """
    Exception raised when :meth:`~PLMObjectController.revise` is called but
    making a revision is not allowed.
    """
    pass

class MetaController(type):
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
        Returns the a controller (subclass of :class:`PLMObjectController`) 
        associated to *type_name* (a string).
        """
        if type_name in cls.controllers_dict:
            return cls.controllers_dict[type_name]
        else:
            # get his model and return his parent controller
            if type_name == "PLMObject":
                # just a security to prevent an infinite recursion
                return PLMObjectController
            else:
                model = models.get_all_plmobjects()[type_name]
                parents = [p for p in model.__bases__ 
                                if issubclass(p, models.PLMObject)]
                return cls.get_controller(parents[0].__name__)

#: shortcut for :meth:`MetaController.get_controller`
get_controller = MetaController.get_controller

class PLMObjectController(object):
    u"""
    Object used to manage a :class:`~plmapp.models.PLMObject` and store his 
    modification in an history
    
    :attributes:
        .. attribute:: object

            The :class:`~openPLM.plmapp.models.PLMObject` managed by the controller

    :param obj: managed object
    :type obj: a subinstance of :class:`~openPLM.plmapp.models.PLMObject`
    :param user: user who modify *obj*
    :type user: :class:`~django.contrib.auth.models.User` 
    """

    __metaclass__ = MetaController

    def __init__(self, obj, user):
        self.object = obj
        self._user = user
        self.__histo = ""

    @classmethod
    def create(cls, reference, type, revision, user, data={}):
        u"""
        This method builds a new :class:`~openPLM.plmapp.models.PLMObject` of
        type *class_* and return a :class:`PLMObjectController` associated to
        the created object.

        Raises :exc:`ValueError` if *reference*, *type* or *revision* are
        empty. Raises :exc:`ValueError` if *type* is not valid.

        :param reference: reference of the objet
        :param type: type of the object
        :param revision: revision of the object
        :param user: user who creates/owns the object
        :param data: a dict<key, value> with informations to add to the plmobject
        :rtype: :class:`PLMObjectController`
        """
        
        if not reference or not type or not revision:
            raise ValueError("Empty value not permitted for reference/type/revision")
        try:
            class_ = models.get_all_plmobjects()[type]
        except KeyError:
            raise ValueError("Incorrect type")
        # create an object
        obj = class_()
        obj.reference = reference
        obj.type = type
        obj.revision = revision
        obj.owner = user
        obj.creator = user
        if data:
            for key, value in data.iteritems():
                if key not in ["reference", "type", "revision"]:
                    setattr(obj, key, value)
        obj.state = models.get_default_state(obj.lifecycle)
        obj.save()
        res = cls(obj, user)
        # record ceation in history
        infos = {"type" : type, "reference" : reference, "revision" : revision}
        infos.update(data)
        details = ",".join("%s : %s" % (k, v) for k, v in infos.items())
        res._save_histo("Create", details)
        return res
        
    @classmethod
    def create_from_form(cls, form, user):
        u"""
        Creates a :class:`PLMObjectController` from *form* and associates *user*
        as the creator/owner of the PLMObject.
        
        This method raises :exc:`ValueError` if *form* is invalid.

        :param form: a django form associated to a model
        :param user: user who creates/owns the object
        :rtype: :class:`PLMObjectController`
        """
        if form.is_valid():
            ref = form.cleaned_data["reference"]
            type = form.Meta.model.__name__
            rev = form.cleaned_data["revision"]
            obj = cls.create(ref, type, rev, user, form.cleaned_data)
            return obj
        else:
            raise ValueError("form is invalid")
        
    def update_from_form(self, form):
        u"""
        Updates :attr:`object` from data of *form*
        
        This method raises :exc:`ValueError` if *form* is invalid.
        """
        if form.is_valid():
            need_save = False
            for key, value in form.cleaned_data.iteritems():
                if key not in ["reference", "type", "revision"]:
                    setattr(self, key, value)
                    need_save = True
            if need_save:
                self.save()
        else:
            raise ValueError("form is invalid")

    def promote(self):
        u"""
        Promotes :attr:`object` in his lifecycle and writes his promotion in
        the history
        """
        if self.object.is_promotable():
            state = self.object.state
            lifecycle = self.object.lifecycle
            lcl = lifecycle.to_states_list()
            try:
                new_state = lcl.next_state(state.name)
                self.object.state = models.State.objects.get_or_create(name=new_state)[0]
                self.object.save()
                self._save_histo("Promote",
                                 "change state from %(first)s to %(second)s" % \
                                     {"first" :state.name, "second" : new_state})

            except IndexError:
                # FIXME raises it ?
                pass

    def demote(self):
        u"""
        Demotes :attr:`object` in his lifecycle and writes his demotion in the
        history
        """
        state = self.object.state
        lifecycle = self.object.lifecycle
        lcl = lifecycle.to_states_list()
        try:
            new_state = lcl.previous_state(state.name)
            self.object.state = models.State.objects.get_or_create(name=new_state)[0]
            self.object.save()
            self._save_histo("Demote", "change state from %(first)s to %(second)s" % \
                    {"first" :state.name, "second" : new_state})
        except IndexError:
            # FIXME raises it ?
            pass

    def __setattr__(self, attr, value):
        if hasattr(self, "object") and hasattr(self.object, attr) and \
           not attr in self.__dict__:
            old_value = getattr(self.object, attr)
            setattr(self.object, attr, value)
            field = self.object._meta.get_field(attr).verbose_name
            message = "%(field)s : changes from '%(old)s' to '%(new)s'" % \
                    {"field" : field, "old" : old_value, "new" : value}
            self.__histo += message + "\n"
        else:
            super(PLMObjectController, self).__setattr__(attr, value)

    def __getattr__(self, attr):
        obj = object.__getattribute__(self, "object")
        if hasattr(self, "object") and hasattr(obj, attr) and \
           not attr in self.__dict__:
            return getattr(obj, attr)
        else:
            return object.__getattribute__(self, attr)

    def save(self):
        u"""
        Saves :attr:`object` and records its history in the database
        """
        self.object.save()
        if self.__histo:
            self._save_histo("Modify", self.__histo) 
            self.__histo = ""

    def _save_histo(self, action, details):
        histo = models.History()
        histo.plmobject = self.object
        histo.action = action
        histo.details = details 
        histo.user = self._user
        histo.save()

    def revise(self, new_revision):
        u"""
        Makes a new revision : duplicates :attr:`object`. The duplicated 
        object's revision is *new_revision*.

        Returns a controller of the new object.
        """

        if models.RevisionLink.objects.filter(old=self.object.pk):
            raise RevisionError("a revision already exists for %s" % self.object)
        data = {}
        fields = self.get_modification_fields() + self.get_creation_fields()
        for attr in fields:
            if attr not in ("reference", "type", "revision"):
                data[attr] = getattr(self.object, attr)
        data["state"] = models.get_default_state(self.lifecycle)
        new_controller = self.create(self.reference, self.type, new_revision, self._user,
                                     data)
        details = "old : %s, new : %s" % (self.object, new_controller.object)
        self._save_histo(models.RevisionLink.ACTION_NAME, details) 
        models.RevisionLink.objects.create(old=self.object, new=new_controller.object)
        return new_controller

    def is_revisable(self):
        """
        Returns True if :attr:`object` is revisable : if :meth:`revise` can be
        called safely
        """
        # objects.get fails if a link does not exist
        # we can revise if any links exist
        try:
            models.RevisionLink.objects.get(old=self.object.pk)
            return False
        except ObjectDoesNotExist:
            return True 
    
    def get_previous_revisions(self):
        try:
            link = models.RevisionLink.objects.get(new=self.object.pk)
            controller = type(self)(link.old, self._user)
            return controller.get_previous_revisions() + [link.old]
        except ObjectDoesNotExist:
            return []

    def get_next_revisions(self):
        try:
            link = models.RevisionLink.objects.get(old=self.object.pk)
            controller = type(self)(link.new, self._user)
            return [link.new] + controller.get_next_revisions()
        except ObjectDoesNotExist:
            return []

    def get_all_revisions(self):
        """
        Returns a list of all revisions, ordered from less recent to most recent
        
        :rtype: list of :class:`~openPLM.plmapp.models.PLMObject`
        """
        return self.get_previous_revisions() + [self.object] +\
               self.get_next_revisions()

Child = namedtuple("Child", "level link")
Parent = namedtuple("Parent", "level link")

class PartController(PLMObjectController):
    u"""
    Controller for :class:`~openPLM.plmapp.models.Part`.

    This controller adds methods to manage Parent-Child links between two
    Parts.
    """

    def add_child(self, child, quantity, order):
        """
        Adds *child* to *self*.

        :param child: added child
        :type child: :class:`~openPLM.plmapp.models.Part`
        :param quantity: amount of *child*
        :type quantity: positive float
        :param order: order
        :type order: positive int
        
        Raises :exc:`ValueError` if *child* is already a child or a parent.
        Raises :exc:`ValueError` if *quantity* or *order* are negative.
        """

        if isinstance(child, PLMObjectController):
            child = child.object
        # check if child is not a parent
        if child == self.object:
            raise ValueError("Can not add child : child is current object")
        parents = (p.link.parent.pk for p in self.get_parents(-1))
        if child.pk in parents:
            raise ValueError("Can not add child %s to %s, it is a parent" %
                                (child, self.object))
        # check if child is not already a direct child
        if child.pk in (c.link.child.pk for c in self.get_children(1)):
            raise ValueError("%s is already a child of %s" % (child, self.object))
        if order < 0 or quantity < 0:
            raise ValueError("Quantity or order is negative")
        # data are valid : create the link
        link = models.ParentChildLink()
        link.parent = self.object
        link.child = child
        link.quantity = quantity
        link.order = order
        link.save()
        # records creation in history
        self._save_histo(link.ACTION_NAME,
                         "parent : %s\nchild : %s" % (self.object, child))

    def delete_child(self, child):
        u"""
        Deletes *child* from current children and records this action in the
        history.

        .. note::
            The link is not destroyed: its end_time is set to now.
        """

        if isinstance(child, PLMObjectController):
            child = child.object
        link = models.ParentChildLink.objects.get(parent=self.object, 
                                                  child=child, end_time=None)
        link.end_time = datetime.today()
        link.save()
        self._save_histo("Delete - %s" % link.ACTION_NAME, "child : %s" % child)

    def modify_child(self, child, new_quantity, new_order):
        """
        Modifies information about *child*.

        :param child: added child
        :type child: :class:`~openPLM.plmapp.models.Part`
        :param new_quantity: amount of *child*
        :type new_quantity: positive float
        :param new_order: order
        :type new_order: positive int
        """
        if isinstance(child, PLMObjectController):
            child = child.object
        if new_order < 0 or new_quantity < 0:
            raise ValueError("Quantity or order is negative")
        link = models.ParentChildLink.objects.get(parent=self.object,
                                                  child=child, end_time=None)
        if link.quantity == new_quantity and link.order == new_order:
            # do not make an update if it is useless
            return
        link.end_time = datetime.today()
        link.save()
        # make a new link
        link2 = models.ParentChildLink(parent=self.object, child=child,
                                       quantity=new_quantity, order=new_order)
        details = ""
        if link.quantity != new_quantity:
            details += "quantity changes from %d to %d\n" % (link.quantity, new_quantity)
        if link.order != new_order:
            details += "order changes from %d to %d" % (link.order, new_order)
        self._save_histo("Modify - %s" % link.ACTION_NAME, details)
        link2.save(force_insert=True)

    def get_children(self, max_level=1, current_level=1, date=None):
        """
        Returns a list of all children at time *date*.
        
        :rtype: list of :class:`Child`
        """

        if max_level != -1 and current_level > max_level:
            return []
        if not date:
            links = models.ParentChildLink.objects.filter(parent=self.object,
                        end_time__exact=None)
        else:
            links = models.ParentChildLink.objects.filter(parent=self.object,
                         ctime__lt=date).exclude(end_time__lt=date)
        res = []
        for link in links.order_by("order", "child__reference"):
            res.append(Child(current_level, link))
            pc = PartController(link.child, self._user)
            res.extend(pc.get_children(max_level, current_level + 1, date))
        return res
    
    def get_parents(self, max_level=1, current_level=1, date=None):
        """
        Returns a list of all parents at time *date*.
        
        :rtype: list of :class:`Parent`
        """

        if max_level != -1 and current_level > max_level:
            return []
        if not date:
            links = models.ParentChildLink.objects.filter(child=self.object,
                        end_time__exact=None)
        else:
            links = models.ParentChildLink.objects.filter(child=self.object,
                         ctime__lt=date).exclude(end_time__lt=date)
        res = []
        for link in links:
            res.append(Parent(current_level, link))
            pc = PartController(link.parent, self._user)
            res.extend(pc.get_parents(max_level, current_level + 1, date))
        return res

    def update_children(self, formset):
        u"""
        Updates children informations with data from *formset*
        
        :param formset:
        :type formset: a modelfactory_formset of 
                        :class:`~plmapp.forms.ModifyChildForm`
        """
        if formset.is_valid():
            for form in formset.forms:
                parent = form.cleaned_data["parent"]
                if parent.pk != self.object.pk:
                    raise ValueError("Bad parent %s (%s expected)" % (parent, self.object))
                delete = form.cleaned_data["delete"]
                child = form.cleaned_data["child"]
                if delete:
                    self.delete_child(child)
                else:
                    quantity = form.cleaned_data["quantity"]
                    order = form.cleaned_data["order"]
                    self.modify_child(child, quantity, order)

    def revise(self, new_revision):
        # same as PLMOBjectController + add children
        new_controller = super(PartController, self).revise(new_revision)
        for level, link in self.get_children(1):
            new_controller.add_child(link.child, link.quantity, link.order)
        return new_controller

class DocumentController(PLMObjectController):
    pass


