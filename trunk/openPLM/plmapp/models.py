#! -*- coding:utf-8 -*-

u"""
Introduction
=============

Models for openPLM

This module contains openPLM's main models.

There are 3 kinds of models:

    * Lifecycle related models :
        - :class:`Lifecycle`
        - :class:`State`
        - :class:`LifecycleStates`
        - there are some functions that may be useful:
            - :func:`get_default_lifecycle`
            - :func:`get_default_state`
    * :class:`History` model
    * PLMOBject models:
        - :class:`PLMObject` is the base class
        - :class:`Part`
        - :class:`Document`
        - functions:
            - :func:`get_all_plmobjects`
            - :func:`get_all_parts`
            - :func:`get_all_documents`
            - :func:`import_models`


Inheritance diagram
=====================

.. inheritance-diagram:: openPLM.plmapp.models
    :parts: 1

Classes and functions
========================
"""

import os
import fnmatch
import datetime
from django.db import models
from django.contrib.auth.models import User

from openPLM.plmapp.lifecycle import LifecycleList

# lifecycle stuff

class State(models.Model):
    u"""
    State : object which represents a state in a lifecycle
    
    .. attribute:: name

        name of the state, must be unique
    """
    name = models.CharField(max_length=50, primary_key=True)

    def __unicode__(self):
        return u'State<%s>' % self.name


class Lifecycle(models.Model):
    u"""
    Lifecycle : object which represents a lifecycle
    
    .. attribute:: name

        name of the lifecycle, must be unique

    .. note::
        A Lifecycle is iterable and each iteration returns a string of
        the next state.

    """
    name = models.CharField(max_length=50, primary_key=True)

    # XXX description field ?

    def __unicode__(self):
        return u'Lifecycle<%s>' % self.name

    def to_states_list(self):
        u"""
        Converts a Lifecycle to a :class:`LifecycleList` (a list of strings)
        """
        
        temp = []
        for lcs in LifecycleStates.objects.filter(lifecycle=self):
            temp.append((lcs.rank, lcs.state.name))
        temp.sort()
        return LifecycleList(self.name, *[state for rank, state in temp])

    def __iter__(self):
        return iter(self.to_states_list())

    @classmethod
    def from_lifecyclelist(cls, cycle):
        u"""
        Builds a Lifecycle from *cycle*. The built object is save in the database.
        This function creates states which were not in the database
        
        :param cycle: the cycle use to build the :class:`Lifecycle`
        :type cycle: :class:`~plmapp.lifecycle.LifecycleList`
        :return: a :class:`Lifecycle`
        """
        
        lifecycle = cls(name=cycle.name)
        lifecycle.save()
        for i, state_name in enumerate(cycle):
            state = State.objects.get_or_create(name=state_name)[0]
            lcs = LifecycleStates(lifecycle=lifecycle, state=state, rank=i)
            lcs.save()
        return lifecycle
                
class LifecycleStates(models.Model):
    u"""
    A LifecycleStates links a :class:`Lifecycle` and a :class:`State`.
    
    The link is made with a field *rank* to order the states.
    """
    lifecycle = models.ForeignKey(Lifecycle, related_name="lifecycle")
    state = models.ForeignKey(State, related_name="State")
    rank = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = (('lifecycle', 'state'),)

    def __unicode__(self):
        return u"LifecycleStates<%s, %s, %d>" % (unicode(self.lifecycle),
                                                 unicode(self.state),
                                                 self.rank)


def get_default_lifecycle():
    u"""
    Returns the default :class:`Lifecycle` used when instanciate a :class:`PLMObject`
    """
    return Lifecycle.objects.all()[0]

def get_default_state(lifecycle=None):
    u"""
    Returns the default :class:`State` used when instanciate a :class:`PLMObject`.
    It's the first state of the default lifecycle.
    """

    if not lifecycle:
        lifecycle = get_default_lifecycle()
    return State.objects.get(name=list(lifecycle)[0])


# PLMobjects

class PLMObject(models.Model):
    u"""
    Base class for :class:`Part` and  :class:`Document`.

    A PLMObject is identified by a triplet reference/type/revision

    :key attributes:
        .. attribute:: reference

            Reference of the :class:`PLMObject`, for example ``YLTG00``
        .. attribute:: type

            Type of the :class:`PLMObject`, for example ``Game``
        .. attribute:: revision
            
            Revision of the :class:`PLMObject`, for example ``a``

    :other attributes:
        .. attribute:: name

            Name of the product, for example ``Game of life``
        .. attribute:: creator

            :class:`~django.contrib.auth.models.User` who created the :class:`PLMObject`
        .. attribute:: creator

            :class:`~django.contrib.auth.models.User` who owns the :class:`PLMObject`
        .. attribute:: ctime

            date of creation of the object (default value : current time)
        .. attribute:: mtime

            date of last modification of the object (automatically field at each save)
        .. attribute:: lifecycle
            
            :class:`Lifecycle` of the object
        .. attribute:: state
            
            Current :class:`State` of the object

    .. note::
        This class is abstract, to create a PLMObject, see :class:`Part` and
        :class:`Document`.

    """

    # key attributes
    reference = models.CharField(max_length=50)
    type = models.CharField(max_length=50)
    revision = models.CharField(max_length=50)

    # other attributes
    name = models.CharField(max_length=100, blank=True,
                            help_text=u"Name of the product")

    creator = models.ForeignKey(User, related_name="%(class)s_creator")
    owner = models.ForeignKey(User, related_name="%(class)s_owner")
    ctime = models.DateTimeField("date of creation", default=datetime.datetime.today,
                                 auto_now_add=False)
    mtime = models.DateTimeField("date of last modification", auto_now=True)

    # state and lifecycle
    lifecycle = models.ForeignKey(Lifecycle, related_name="%(class)s_lifecyle",
                                 default=get_default_lifecycle)
    state = models.ForeignKey(State, related_name="%(class)s_lifecyle",
                                 default=get_default_state)

    
    class Meta:
        # keys in the database
        unique_together = (('reference', 'type', 'revision'),)

    def __unicode__(self):
        return u"%s<%s/%s/%s>" % (type(self).__name__, self.reference, self.type,
                                  self.revision)

    def is_promotable(self):
        u"""
        Returns True if object is promotable

        .. note::
            This method is abstract and raises :exc:`NotImplementedError`.
            This method must be overriden.
        """
        raise NotImplementedError()

    
    @property
    def attributes(self):
        u"Attributes to display in `Attributes view`"
        return ["name",  "creator", "owner", "ctime", "mtime"]

    @property
    def menu_items(self):
        "menu items to choose a view"
        return ["attributes", "lifecycle", "revisions", "history"]

    @classmethod
    def excluded_creation_fields(cls):
        "Returns fields which should not be available in a creation form"
        return ["owner", "creator", "ctime", "mtime"]

    @classmethod
    def get_creation_fields(cls):
        "Returns fields which should be displayed in a creation form"
        fields = ["reference", "type", "revision", "lifecycle", "state"]
        for field in cls().attributes:
            if field not in cls.excluded_creation_fields():
                fields.append(field)
        return fields

    @classmethod
    def excluded_modification_fields(cls):
        "Returns fields which should not be available in a modification form"
        return ["creator", "ctime", "mtime"]

    @classmethod
    def get_modification_fields(cls):
        "Returns fields which should be displayed in a modification form"
        fields = []
        for field in cls().attributes:
            if field not in cls.excluded_modification_fields():
                fields.append(field)
        return fields

# parts stuff

class Part(PLMObject):

    @property
    def menu_items(self):
        items = list(super(Part, self).menu_items)
        items.extend(["BOM-child", "parents"])
        return items

    def is_promotable(self):
        # TODO check parent/child links
        return True


class PlasticPart(Part):

    mass = models.PositiveIntegerField(blank=True, null=True)

    @property
    def attributes(self):
        attrs = list(super(PlasticPart, self).attributes)
        attrs.extend(["mass"])
        return attrs

class RedPlasticPart(PlasticPart):
    pass


def _get_all_subclasses(base, d):
    if base.__name__ not in d:
        d[base.__name__] = base
    for part in base.__subclasses__():
        _get_all_subclasses(part, d)

def get_all_parts():
    u"""
    Returns a dict<part_name, part_class> of all available :class:`Part` classes
    """
    res = {}
    _get_all_subclasses(Part, res)
    return res

# document stuff

class Document(PLMObject):

    def is_promotable(self):
        # TODO check file
        return True


def get_all_documents():
    u"""
    Returns a dict<doc_name, doc_class> of all available :class:`Document` classes
    """
    res = {}
    _get_all_subclasses(Document, res)
    return res

def get_all_plmobjects():
    u"""
    Returns a dict<name, class> of all available :class:`PLMObject` subclasses
    """

    res = {}
    _get_all_subclasses(PLMObject, res)
    del res["PLMObject"]
    return res


# history stuff
class History(models.Model):
    u"""
    History model.
    This model records all events related to :class:`PLMObject`

    :model attributes:
        .. attribute:: plmobject

            :class:`PLMObject` of the event
        .. attribute:: action

            type of action (see :attr:`ACTIONS`)
        .. attribute:: details
        
            type of action (see :attr:`ACTIONS`)
        .. attribute:: date
        
            date of the event
        .. attribute:: user
        
            :class:`~django.contrib.auth.models.User` who maded the event

    :class attribute:
    """
    #: some actions available in the admin interface
    ACTIONS = (
        ("Create", "Create"),
        ("Delete", "Delete"),
        ("Modify", "Modify"),
        ("Revise", "Revise"),
        ("Promote", "Promote"),
        ("Demote", "Demote"),
    )
    
    plmobject = models.ForeignKey(PLMObject, related_name="%(class)s_plmobject")
    action = models.CharField(max_length=50, choices=ACTIONS)
    details = models.TextField()
    date = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, related_name="%(class)s_user")

    def __unicode__(self):
        return "History<%s, %s, %s>" % (self.plmobject, self.date, self.action)

# link stuff

class Link(models.Model):
    u"""
    Link base class.

    This class represents a link between two :class:`PLMObject`
    """


    ACTION_NAME = "Link"
    OBJECT1_TYPE = PLMObject
    OBJECT2_TYPE = PLMObject
    object1 = models.ForeignKey(PLMObject, related_name="%(class)s_object1")
    object2 = models.ForeignKey(PLMObject, related_name="%(class)s_object2")
    #: type is automatically set, it should not be modified
    type = models.CharField(max_length=60, editable=False)

    def __init__(self, *args, **kwargs):
        kwargs["type"] = self.__class__.__name__
        super(Link, self).__init__(*args, **kwargs)
    
    def save(self, force_insert=False, force_update=False):
        if self.type != type(self).__name__:
            raise ValueError("Bad value for type, should be %s", type(self).__name__)
               
        super(Link, self).save(force_insert, force_update)

    class Meta:
        unique_together = ("object1", "object2", "type")


class RevisionLink(Link):
    
    ACTION_NAME = "Link : revision"
    
    new = Link.object1
    old = Link.object2

class ParentChildLink(Link):

    ACTION_NAME = "Link : parent-child"
    OBJECT1_TYPE = Part
    OBJECT2_TYPE = Part

    quantity = models.PositiveIntegerField(default=lambda: 1)
    order = models.PositiveIntegerField(default=lambda: 1)
    
    def get_parent(self):
        return self.OBJECT1_TYPE.objects.get(id=self.object1.pk)
    def set_parent(self, parent):
        self.object1 = parent
    parent = property(get_parent, set_parent)

    def get_child(self):
        return self.OBJECT2_TYPE.objects.get(id=self.object2.pk)
    def set_child(self, child):
        self.object2 = child
    child = property(get_child, set_child)

# import_models should be the last function

def import_models(force_reload=False):
    u"""
    Imports recursively all modules in directory *plmapp/customized_models*
    """

    MODELS_DIR = "customized_models"
    IMPORT_ROOT = "openPLM.plmapp.%s" % MODELS_DIR
    if force_reload or not hasattr(import_models, "done"):
        import_models.done = True
        models_dir = os.path.join(os.path.split(__file__)[0], MODELS_DIR)
        for root, dirs, files in os.walk(models_dir):
            for module in fnmatch.filter(files, "*.py"):
                module_name = os.path.splitext(os.path.basename(module))[0]
                import_dir = root.split(MODELS_DIR, 1)[-1].replace(os.path.sep, ".")
                import_name = "%s.%s.%s" % (IMPORT_ROOT, import_dir, module_name)
                import_name = import_name.replace("..", ".")
                try:
                    __import__(import_name, globals(), locals(), [], -1)
                except ImportError, exc:
                    print "Exception in import_models", exc
                except StandardError, exc:
                    print "Exception in import_models", type(exc), exc
import_models()

