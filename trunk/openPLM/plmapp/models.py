#! -*- coding:utf-8 -*-

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

u"""
Introduction
=============

Models for openPLM

This module contains openPLM's main models.

There are 5 kinds of models:
    * :class:`UserProfile`
    * Lifecycle related models :
        - :class:`Lifecycle`
        - :class:`State`
        - :class:`LifecycleStates`
        - there are some functions that may be useful:
            - :func:`get_default_lifecycle`
            - :func:`get_default_state`
    * History models:
        - :class:`AbstractHistory` model
        - :class:`History` model
        - :class:`UserHistory` model
    * PLMObject models:
        - :class:`PLMObject` is the base class
        - :class:`Part`
        - :class:`Document` and related classes:
            - :class:`DocumentStorage` (see also :obj:`docfs`)
            - :class:`DocumentFile`
        - functions:
            - :func:`get_all_plmobjects`
            - :func:`get_all_parts`
            - :func:`get_all_documents`
            - :func:`import_models`
    * :class:`Link` models:
        - :class:`RevisionLink`
        - :class:`ParentChildLink`
        - :class:`DocumentPartLink`
        - :class:`DelegationLink`
        - :class:`PLMObjectUserLink`


Inheritance diagram
=====================

.. inheritance-diagram:: openPLM.plmapp.models
    :parts: 1

Classes and functions
========================
"""

import os
import string
import random
import hashlib
import fnmatch
import datetime

import kjbuckets
from django.db import models
from django.db.models.query import QuerySet
from django.db.models.signals import post_save
from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core.files.storage import FileSystemStorage
from django.utils.encoding import iri_to_uri
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop
from django.forms.util import ErrorList

from openPLM.plmapp.units import UNITS, DEFAULT_UNIT
from openPLM.plmapp.lifecycle import LifecycleList
from openPLM.plmapp.utils import level_to_sign_str, memoize_noarg


# user stuff

class UserProfile(models.Model):
    """
    Profile for a :class:`~django.contrib.auth.models.User`
    """
    user = models.ForeignKey(User, unique=True)
    #: True if user is an administrator
    is_administrator = models.BooleanField(default=False, blank=True)
    #: True if user is a contributor
    is_contributor = models.BooleanField(default=False, blank=True)
    
    @property
    def is_viewer(self):
        u"""
        True if user is just a viewer, i.e: not an adminstrator and not a
        contributor.
        """
        return not (self.is_administrator or self.is_contributor)

    def __unicode__(self):
        return u"UserProfile<%s>" % self.user.username

    @property
    def plmobject_url(self):
        return iri_to_uri("/user/%s/" % self.user.username)

    @property
    def rank(self):
        u""" Rank of the user: "adminstrator", "contributor" or "viewer" """
        if self.is_administrator:
            return _("administrator")
        elif self.is_contributor:
            return _("contributor")
        else:
            return _("viewer")

    @property
    def attributes(self):
        u"Attributes to display in `Attributes view`"
        return ["first_name", "last_name", "email",  "creator", "owner",
                "ctime", "mtime", "rank"]

    @property
    def menu_items(self):
        "menu items to choose a view"
        return ["attributes", "history", "parts-doc-cad", "delegation",
                "groups"]

    @classmethod
    def excluded_creation_fields(cls):
        "Returns fields which should not be available in a creation form"
        return ["owner", "creator", "ctime", "mtime"]
   

def add_profile(sender, instance, created, **kwargs):
    """ function called when an user is created to add his profile """
    if sender == User and created:
        profile = UserProfile(user=instance)
        profile.save()

if __name__ == "openPLM.plmapp.models":
    post_save.connect(add_profile, sender=User)


class GroupInfo(Group):
    u"""
    Class that stores additional data on a :class:`Group`.
    """

    description = models.TextField(blank=True)
    creator = models.ForeignKey(User, related_name="%(class)s_creator")
    
    owner = models.ForeignKey(User, verbose_name=_("owner"), 
                              related_name="%(class)s_owner")
    ctime = models.DateTimeField(_("date of creation"), default=datetime.datetime.today,
                                 auto_now_add=False)
    mtime = models.DateTimeField(_("date of last modification"), auto_now=True)

    def __init__(self, *args, **kwargs):
        if "__fake__" not in kwargs:
            super(GroupInfo, self).__init__(*args, **kwargs)

    @property
    def plmobject_url(self):
        return iri_to_uri("/group/%s/" % self.name)

    @property
    def attributes(self):
        u"Attributes to display in `Attributes view`"
        return ["name", "description", "creator", "owner",
                "ctime", "mtime"]

    @property
    def menu_items(self):
        "menu items to choose a view"
        return ["attributes", "history", "users", "objects"]

    @classmethod
    def excluded_creation_fields(cls):
        "Returns fields which should not be available in a creation form"
        return ["owner", "creator", "ctime", "mtime"]

    @classmethod
    def get_creation_fields(cls):
        """
        Returns fields which should be displayed in a creation form.

        By default, it returns :attr:`attributes` less attributes returned by
        :meth:`excluded_creation_fields`
        """
        fields = []
        for field in cls(__fake__=True).attributes:
            if field not in cls.excluded_creation_fields():
                fields.append(field)
        return fields

    @classmethod
    def excluded_modification_fields(cls):
        """
        Returns fields which should not be available in a modification form
        
        By default, it returns :attr:`attributes` less attributes returned by
        :meth:`excluded_modification_fields`
        """
        return [ugettext_noop("name"), ugettext_noop("creator"),
                ugettext_noop("owner"), ugettext_noop("ctime"),
                ugettext_noop("mtime")]

    @classmethod
    def get_modification_fields(cls):
        "Returns fields which should be displayed in a modification form"
        fields = []
        for field in cls(__fake__=True).attributes:
            if field not in cls.excluded_modification_fields():
                fields.append(field)
        return fields

    @property
    def is_editable(self):
        return True

    def get_attributes_and_values(self):
        return [(attr, getattr(self, attr)) for attr in self.attributes]


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

    .. attribute:: official_state

        *official* :class:`State` of the lifecycle

    .. note::
        A Lifecycle is iterable and each iteration returns a string of
        the next state.

    .. seealso:: :class:`~plmapp.lifecycle.LifecycleList`
        A class that simplifies the usage of a LifeCycle

    """

    name = models.CharField(max_length=50, primary_key=True)
    official_state = models.ForeignKey(State)

    def __init__(self, *args, **kwargs):
        super(Lifecycle, self).__init__(*args, **kwargs)
        # keep a cache of some values: Lifecycle are most of the time
        # read-only objects, and there are no valid reasons to modify a
        # lifecycle in a production environment
        self._first_state = None
        self._last_state = None
        self._states_list = None

    def __unicode__(self):
        return u'Lifecycle<%s>' % self.name

    def to_states_list(self):
        u"""
        Converts a Lifecycle to a :class:`LifecycleList` (a list of strings)
        """
        if self._states_list is None:
            lcs = self.lifecyclestates_set.order_by("rank")
            self._states_list = LifecycleList(self.name, self.official_state.name,
                    *lcs.values_list("state__name", flat=True))
        return LifecycleList(self.name, self.official_state, *self._states_list)

    @property
    def first_state(self):
        if self._first_state is None:
            self._first_state = self.lifecyclestates_set.order_by('rank')[0].state
        return self._first_state
    
    @property
    def last_state(self):
        if self._last_state is None:
            self._last_state = self.lifecyclestates_set.order_by('-rank')[0].state
        return self._last_state

    @property
    def nb_states(self):
        return self.lifecyclestates_set.count()

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
        
        lifecycle = cls(name=cycle.name,
            official_state=State.objects.get_or_create(name=cycle.official_state)[0])
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
    lifecycle = models.ForeignKey(Lifecycle)
    state = models.ForeignKey(State)
    rank = models.PositiveSmallIntegerField()

    class Meta:
        unique_together = (('lifecycle', 'state'),)

    def __unicode__(self):
        return u"LifecycleStates<%s, %s, %d>" % (unicode(self.lifecycle),
                                                 unicode(self.state),
                                                 self.rank)

@memoize_noarg
def get_default_lifecycle():
    u"""
    Returns the default :class:`Lifecycle` used when instanciate a :class:`PLMObject`
    """
    return Lifecycle.objects.all()[0]

_default_states_cache = {}
def get_default_state(lifecycle=None):
    u"""
    Returns the default :class:`State` used when instanciate a :class:`PLMObject`.
    It's the first state of the default lifecycle.
    """

    if not lifecycle:
        lifecycle = get_default_lifecycle()
    state = _default_states_cache.get(lifecycle.name, None)
    if state is None:
        state = lifecycle.first_state
        _default_states_cache[lifecycle.name] = state
    return state

# PLMobjects

class PLMObject(models.Model):
    u"""
    Base class for :class:`Part` and :class:`Document`.

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
        .. attribute:: group

            :class:`GroupInfo` that owns the object

    .. note::

        This class is abstract, to create a PLMObject, see :class:`Part` and
        :class:`Document`.

    """

    # key attributes
    reference = models.CharField(_("reference"), max_length=50, db_index=True)
    type = models.CharField(_("type"), max_length=50)
    revision = models.CharField(_("revision"), max_length=50)

    # other attributes
    name = models.CharField(_("name"), max_length=100, blank=True,
                            help_text=_(u"Name of the product"))

    creator = models.ForeignKey(User, verbose_name=_("creator"), 
                                related_name="%(class)s_creator")
    owner = models.ForeignKey(User, verbose_name=_("owner"), 
                              related_name="%(class)s_owner")
    ctime = models.DateTimeField(_("date of creation"), default=datetime.datetime.today,
                                 auto_now_add=False)
    mtime = models.DateTimeField(_("date of last modification"), auto_now=True)
    group = models.ForeignKey(GroupInfo, related_name="%(class)s_group")

    # state and lifecycle
    lifecycle = models.ForeignKey(Lifecycle, verbose_name=_("lifecycle"), 
                                  related_name="%(class)s_lifecyle",
                                  default=get_default_lifecycle)
    state = models.ForeignKey(State, verbose_name=_("state"),
                              related_name="%(class)s_lifecyle",
                              default=get_default_state)
    
    
    class Meta:
        # keys in the database
        unique_together = (('reference', 'type', 'revision'),)
        ordering = ["type", "reference", "revision"]

    def __init__(self, *args, **kwargs):
        # little hack:
        # get_creation_fields is a class method but it needs to create
        # an instance, this hacks avoids calls to default value functions
        if "__fake__" not in kwargs:
            super(PLMObject, self).__init__(*args, **kwargs)
        self._promotion_errors = None

    def __unicode__(self):
        return u"%s<%s/%s/%s>" % (type(self).__name__, self.reference, self.type,
                                  self.revision)

    def _is_promotable(self):
        """
        Returns True if the object's state is the last state of its lifecycle.
        """
        self._promotion_errors = ErrorList()
        if self.lifecycle.last_state == self.state:
            self._promotion_errors.append(_(u"The object is at its last state."))
            return False
        return True

    def is_promotable(self):
        u"""
        Returns True if object is promotable

        .. note::
            This method is abstract and raises :exc:`NotImplementedError`.
            This method must be overriden.
        """
        raise NotImplementedError()

    def _get_promotion_errors(self):
        """ Returns an :class:`ErrorList` of promotion errors.
        Calls :meth:`is_promotable()` if it has not already been called.
        """
        if self._promotion_errors is None:
            self.is_promotable()
        return self._promotion_errors
    promotion_errors = property(_get_promotion_errors)

    @property
    def is_editable(self):
        """
        True if the object is not in a non editable state
        (for example, in an official or deprecated state).
        """
        lcs = self.lifecycle.lifecyclestates_set.only("rank")
        current_rank = lcs.get(state=self.state).rank
        official_rank = lcs.get(state=self.lifecycle.official_state).rank
        return current_rank < official_rank
    
    def get_current_sign_level(self):
        """
        Returns the current sign level that an user must have to promote this
        object.
        """
        rank = LifecycleStates.objects.get(state=self.state,
                            lifecycle=self.lifecycle).rank
        return level_to_sign_str(rank) 
    
    def get_previous_sign_level(self):
        """
        Returns the current sign level that an user must have to demote this
        object.
        """
        rank = LifecycleStates.objects.get(state=self.state,
                            lifecycle=self.lifecycle).rank
        return level_to_sign_str(rank - 1) 
   
    @property
    def is_part(self):
        if self.type in get_all_plmobjects():
            return issubclass(get_all_plmobjects()[self.type], Part)
        return False

    @property
    def is_document(self):
        if self.type in get_all_plmobjects():
            return issubclass(get_all_plmobjects()[self.type], Document)
        return False
    
    @property
    def is_official(self):
        u"Returns True if document's state is official."""
        return self.state == self.lifecycle.official_state

    @property
    def attributes(self):
        u"Attributes to display in `Attributes view`"
        return ["type", "reference", "revision", "name", "creator", "owner",
                "group", "ctime", "mtime"]

    @property
    def menu_items(self):
        "Menu items to choose a view"
        return [ugettext_noop("attributes"), ugettext_noop("lifecycle"),
                ugettext_noop("revisions"), ugettext_noop("history"),
                ugettext_noop("management")]

    @classmethod
    def excluded_creation_fields(cls):
        "Returns fields which should not be available in a creation form"
        return ["owner", "creator", "ctime", "mtime", "state"]

    @property
    def plmobject_url(self):
        url = u"/object/%s/%s/%s/" % (self.type, self.reference, self.revision) 
        return iri_to_uri(url)
    
    @classmethod
    def get_creation_fields(cls):
        """
        Returns fields which should be displayed in a creation form.

        By default, it returns :attr:`attributes` less attributes returned by
        :meth:`excluded_creation_fields`
        """
        fields = ["reference", "type", "revision", "lifecycle"]
        for field in cls(__fake__=True).attributes:
            if field not in cls.excluded_creation_fields():
                fields.append(field)
        return fields

    @classmethod
    def excluded_modification_fields(cls):
        """
        Returns fields which should not be available in a modification form
        """
        return [ugettext_noop("type"), ugettext_noop("reference"),
                ugettext_noop("revision"),
                ugettext_noop("ctime"), ugettext_noop("creator"),
                ugettext_noop("owner"), ugettext_noop("ctime"),
                ugettext_noop("mtime"), ugettext_noop("group")]

    @classmethod
    def get_modification_fields(cls):
        """
        Returns fields which should be displayed in a modification form
        
        By default, it returns :attr:`attributes` less attributes returned by
        :meth:`excluded_modification_fields`
        """
        fields = []
        for field in cls(__fake__=True).attributes:
            if field not in cls.excluded_modification_fields():
                fields.append(field)
        return fields

    def get_attributes_and_values(self):
        return [(attr, getattr(self, attr)) for attr in self.attributes]

    def get_leaf_object(self):
        return get_all_plmobjects()[self.type].objects.get(id=self.id)

# parts stuff

class Part(PLMObject):
    """
    Model for parts
    """

    @property
    def menu_items(self):
        items = list(super(Part, self).menu_items)
        items.extend([ugettext_noop("BOM-child"), ugettext_noop("parents"), 
                      ugettext_noop("doc-cad")])
        return items

    def is_promotable(self):
        """
        Returns True if the part is promotable. 
        
        A part is promotable if:
            
            #. its state is not the last state of its lifecycle
            
            #. if the part is not editable (its state is official).
            
            #. the part is editable and:

                #. there is a next state in its lifecycle and if its children
                    which have the same lifecycle are in a state as mature as
                    the object's state.  

                #. if the part has no children, there is at least one official
                   document attached to it.
        """
        if not self._is_promotable():
            return False
        if not self.is_editable:
            return True
        # check children
        children = self.parentchildlink_parent.filter(end_time__exact=None).only("child")
        lcs = self.lifecycle.to_states_list()
        rank = lcs.index(self.state.name)
        for link in children:
            child = link.child
            if child.lifecycle == self.lifecycle:
                rank_c = lcs.index(child.state.name)
                if rank_c == 0 or rank_c < rank:
                    self._promotion_errors.append(_("Some children are at a lower or draft state."))
                    return False
        if not children:
            # check that at least one document is attached and its state is official
            # see ticket #57
            found = False
            links = self.documentpartlink_part.all()
            for link in links:
                found = link.document.is_official
                if found:
                    break
            if not found:
                self._promotion_errors.append(_("There are no official documents attached."))
            return found
        return True

    @property
    def is_part(self):
        return True
    
    @property
    def is_document(self):
        return False

def _get_all_subclasses(base, d):
    if base.__name__ not in d:
        d[base.__name__] = base
    for part in base.__subclasses__():
        _get_all_subclasses(part, d)

@memoize_noarg
def get_all_parts():
    u"""
    Returns a dict<part_name, part_class> of all available :class:`Part` classes
    """
    res = {}
    _get_all_subclasses(Part, res)
    return res

# document stuff
class DocumentStorage(FileSystemStorage):
    """
    File system storage which stores files with a specific name
    """
    def get_available_name(self, name):
        """
        Returns a path for a file *name*, the path always refers to a file
        which do not exist.
        
        The path is computed as follow:
            #. a directory which name is the last extension of *name*.
               For example, it is :file:`gz` if *name* is :file:`a.tar.gz`.
               If *name* does not have an extension, the directory is 
               :file:`no_ext/`.
            #. a file name with 4 parts:
                #. the md5 sum of *name*
                #. a dash separator: ``-``
                #. a random part with 3 characters in ``[a-z0-9]``
                #. the extension, like :file:`.gz`
            
            For example, if *name* is :file:`my_file.tar.gz`,
            a possible output is:

                :file:`gz/c7bfe8d00ea6e7138215ebfafff187af-jj6.gz`

            If *name* is :file:`my_file`, a possible output is:

                :file:`no_ext/59c211e8fc0f14b21c78c87eafe1ab72-dhh`
        """
       
        def rand():
            r = ""
            for i in xrange(3):
                r += random.choice(string.ascii_lowercase + string.digits)
            return r
        basename = os.path.basename(name)
        base, ext = os.path.splitext(basename)
        ext2 = ext.lstrip(".").lower() or "no_ext"
        md5 = hashlib.md5()
        md5.update(basename)
        md5_value = md5.hexdigest() + "-%s" + ext
        path = os.path.join(ext2, md5_value % rand())
        while os.path.exists(os.path.join(self.location, path)):
            path = os.path.join(ext2, md5_value % rand())
        return path

#: :class:`DocumentStorage` instance which stores files in :const:`settings.DOCUMENTS_DIR`
docfs = DocumentStorage(location=settings.DOCUMENTS_DIR)
#: :class:`FileSystemStorage` instance which stores thumbnails in :const:`settings.THUMBNAILS_DIR`
thumbnailfs = FileSystemStorage(location=settings.THUMBNAILS_DIR,
        base_url=settings.THUMBNAILS_URL)

class DocumentFile(models.Model):
    """
    Model which stores informations of a file link to a :class:`Document`
    
    :model attributes:
        .. attribute:: filename
            
            original filename
        .. attribute:: file
            
            file stored in :obj:`docfs`
        .. attribute:: size
            
            size of the file in Byte
        .. attribute:: locked

            True if the file is locked
        .. attribute:: locker
            
            :class:`~django.contrib.auth.models.User` who locked the file,
            None, if the file is not locked
        .. attribute document

            :class:`Document` linked to the file
    """
    filename = models.CharField(max_length=200)
    file = models.FileField(upload_to=".", storage=docfs)
    size = models.PositiveIntegerField()
    thumbnail = models.ImageField(upload_to=".", storage=thumbnailfs,
                                 blank=True, null=True)
    locked = models.BooleanField(default=lambda: False)
    locker = models.ForeignKey(User, null=True, blank=True,
                               default=lambda: None)
    document = models.ForeignKey('Document')

    def __unicode__(self):
        return u"DocumentFile<%s, %s>" % (self.filename, self.document)

class Document(PLMObject):
    """
    Model for documents
    """

    @property
    def files(self):
        "Queryset of all :class:`DocumentFile` linked to self"
        return self.documentfile_set.all()

    def is_promotable(self):
        """
        Returns True if the object is promotable. A documentt is promotable
        if there is a next state in its lifecycle and if it has at least
        one file and if none of its files are locked.
        """
        if not self._is_promotable():
            return False
        if not bool(self.files):
            self._promotion_errors.append(_("This document has no files."))
            return False
        if bool(self.files.filter(locked=True)):
            self._promotion_errors.append(_("Some files are locked."))
            return False
        return True

    @property
    def menu_items(self):
        items = list(super(Document, self).menu_items)
        items.insert(0, ugettext_noop("files"))
        items.append(ugettext_noop("parts"))
        return items

    @property
    def is_part(self):
        return False
    
    @property
    def is_document(self):
        return True


@memoize_noarg
def get_all_documents():
    u"""
    Returns a dict<doc_name, doc_class> of all available :class:`Document` classes
    """
    res = {}
    _get_all_subclasses(Document, res)
    return res

@memoize_noarg
def get_all_plmobjects():
    u"""
    Returns a dict<name, class> of all available :class:`PLMObject` subclasses
    """

    res = {}
    _get_all_subclasses(PLMObject, res)
    res["Group"] = GroupInfo
    del res["PLMObject"]
    return res

@memoize_noarg
def get_all_users_and_plmobjects():
    res = {}
    _get_all_subclasses(User, res)
    res.update(get_all_plmobjects())
    return res

@memoize_noarg
def get_all_userprofiles_and_plmobjects():
    res = {}
    _get_all_subclasses(UserProfile, res)
    res.update(get_all_plmobjects())
    return res

# history stuff
class AbstractHistory(models.Model):
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
    
    class Meta:
        abstract = True

    action = models.CharField(max_length=50, choices=ACTIONS)
    details = models.TextField()
    date = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, related_name="%(class)s_user")

    def __unicode__(self):
        return "History<%s, %s, %s>" % (self.plmobject, self.date, self.action)

    def get_day(self):
        return datetime.date(self.date.year, self.date.month, self.date.day) 

class History(AbstractHistory):
    plmobject = models.ForeignKey(PLMObject)

class UserHistory(AbstractHistory):
    plmobject = models.ForeignKey(User)

class GroupHistory(AbstractHistory):
    plmobject = models.ForeignKey(Group)

# link stuff

class Link(models.Model):
    u"""
    Abstract link base class.

    This class represents a link between two :class:`PLMObject`
    
    :model attributes:
        .. attribute:: ctime

            date of creation of the link (automatically set)

    :class attributes:
        .. attribute:: ACTION_NAME

            an identifier used to set :attr:`History.action` field
    """

    ctime = models.DateTimeField(auto_now_add=True)

    ACTION_NAME = "Link"
    class Meta:
        abstract = True

class RevisionLink(Link):
    """
    Link between two revisions of a :class:`PLMObject`
    
    :model attributes:
        .. attribute:: old

            old revision (a :class:`PLMObject`)
        .. attribute:: new

            new revision (a :class:`PLMObject`)
    """
    
    ACTION_NAME = "Link : revision"
    old = models.ForeignKey(PLMObject, related_name="%(class)s_old")    
    new = models.ForeignKey(PLMObject, related_name="%(class)s_new")
    
    class Meta:
        unique_together = ("old", "new")

    def __unicode__(self):
        return u"RevisionLink<%s, %s>" % (self.old, self.new)
    

class ParentChildLink(Link):
    """
    Link between two :class:`Part`: a parent and a child
    
    :model attributes:
        .. attribute:: parent

            a :class:`Part`
        .. attribute:: child

            a :class:`Part`
        .. attribute:: quantity
            
            amount of child (a positive float)
        .. attribute:: unit
            
            unit of the quantity
        .. attribute:: order
            
            positive integer
        .. attribute:: end_time
            
            date of end of the link, None if the link is still alive

    """

    ACTION_NAME = "Link : parent-child"

    parent = models.ForeignKey(Part, related_name="%(class)s_parent")    
    child = models.ForeignKey(Part, related_name="%(class)s_child")    
    quantity = models.FloatField(default=lambda: 1)
    unit = models.CharField(max_length=4, choices=UNITS,
            default=lambda: DEFAULT_UNIT)
    order = models.PositiveSmallIntegerField(default=lambda: 1)
    end_time = models.DateTimeField(blank=True, null=True, default=lambda: None)
    
    class Meta:
        unique_together = ("parent", "child", "end_time")

    def __unicode__(self):
        return u"ParentChildLink<%s, %s, %f, %s, %d>" % (self.parent, self.child,
                                 self.quantity, self.unit, self.order)

    def get_shortened_unit(self):
        """ Returns unit as a human readable string.
        If :attr:`unit` equals to "-", returns an empty string.
        """
        if self.unit == "-":
            return u""
        return self.get_unit_display()

    @property
    def extensions(self):
        """ Returns a queryset of bound :class:`ParentChildLinkExtension`. """
        return ParentChildLinkExtension.children.filter(link=self)

    def get_extension_data(self):
        """
        Returns a dictionary of extension data. The returned value can be passed
        as a valid arguement to :meth:`clone`.
        """

        extension_data = {}
        for ext in self.extensions:
            if ext.one_per_link():
                extension_data[ext._meta.module_name] = ext.to_dict()
        return extension_data

    def clone(self, save=False, extension_data=None, **kwargs):
        u"""
        Clone this link.

        It is possible to pass additional arguement to override some original
        values.

        :param save: If True, the cloned link and its extensions are saved
        :param extension_data: dictionary PCLE module name -> data of data
            that are given to :meth:`ParentChildLinkExtension.clone`.
        
        :return: a tuple (cloned link, list of cloned extensions)

        Example::

            >>> print link
            ParentChildLink<Part<PART_2/MotherBoard/a>, Part<ttd/RAM/a>, 4.000000, -, 10>
            >>> link.extensions
            [<ReferenceDesignator: ReferenceDesignator<m1,m2,>>]
            >>> clone, ext = link.clone(False,
            ...    {"referencedesignator" : { "reference_designator" : "new_value"}},
            ...    quantity=51)
            >>> print clone
            ParentChildLink<Part<PART_2/MotherBoard/a>, Part<ttd/RAM/a>, 51.000000, -, 10>
            >>> print ext
            [<ReferenceDesignator: ReferenceDesignator<new_value>>]
            
        """
        # original data
        data = dict(parent=self.parent, child=self.child,
                quantity=self.quantity, order=self.order, unit=self.unit,
                end_time=self.end_time)
        # update data from kwargs
        for key, value in kwargs.iteritems():
            if key in data:
                data[key] = value
        link = ParentChildLink(**data)
        if save:
            link.save()
        # clone the extensions
        extensions = []
        extension_data = extension_data or {}
        for ext in self.extensions:
            extensions.append(ext.clone(link, save, 
                **extension_data.get(ext._meta.module_name, {})))
        return link, extensions


class ChildQuerySet(QuerySet):
    def iterator(self):
        for obj in super(ChildQuerySet, self).iterator():
            yield obj.get_child_object()


class ChildManager(models.Manager):
    def get_query_set(self):
        return ChildQuerySet(self.model)


class ParentModel(models.Model):
    _child_name = models.CharField(max_length=100, editable=False)

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        self._child_name = self.get_child_name()
        super(ParentModel, self).save(*args, **kwargs)

    def get_child_name(self):
        if type(self) is self.get_parent_model():
            return self._child_name
        return self.get_parent_link().related_query_name()

    def get_child_object(self):
        return getattr(self, self.get_child_name())

    def get_parent_link(self):
        return self._meta.parents[self.get_parent_model()]

    def get_parent_model(self):
        raise NotImplementedError

    def get_parent_object(self):
        return getattr(self, self.get_parent_link().name)

registered_PCLEs = []
class ParentChildLinkExtension(ParentModel):
    """
    Extension of a :class:`ParentChildLink` used to store additional data.

    This class is abstract, subclass must define the :meth:`clone` method,
    add at least one field (or it would be useless) and may override
    :meth:`get_visible_fields` or :meth:`get_editable_fields`.

    .. seealso::
    
        :ref:`bom_extensions` explains how to subclass this class.
    """

    #! link bound to the PCLE
    link = models.ForeignKey(ParentChildLink, related_name="%(class)s_link")

    objects = models.Manager()
    children = ChildManager()

    @classmethod
    def get_visible_fields(cls):
        """
        Returns the list of visible fieldnames.
        
        By default, returns an empty list.
        """
        return []

    @classmethod
    def get_editable_fields(cls):
        """
        Returns the list of editable fields.

        By default, returns :meth:`get_visible_fields`.
        """
        return list(cls.get_visible_fields())

    @classmethod
    def one_per_link(cls):
        """ Returns True if only one extension should be created per link.

        By default return True if :meth:`get_visible_fields` returns a
        non empty list."""
        return bool(cls.get_visible_fields())
    
    @classmethod
    def apply_to(cls, parent):
        """
        Returns True if this extension applies to *parent*.

        :param parent: part which will have a new child
        :type parent: :class:`Part` (its most specific subclass).
        
        Returns True by default.
        """
        return True

    def clone(self, link, save=False, **data):
        """
        Clone this extension.
        
        **Subclass must define its implementation.** and respect the
        following specification:

        :param link: the new cloned link, the cloned extension must be
                     bound to it
        :type link: :class:`ParentChildLink`
        :param save: True if the cloned extension must be saved, False
                     (the default) if it must not be saved.
        :type save: boolean
        :param data: additional data that override the original values
        
        :return: the cloned extension
        """
        raise NotImplementedError

    def get_parent_model(self):
        return ParentChildLinkExtension

    def to_dict(self):
        """
        Returns a dictionary fieldnames -> value that can be safely passed as
        a kwargument to :meth:`clone` and that is used to compare two
        extensions. 
        """
        d = {}
        for field in self._meta.get_all_field_names():
            if field not in ("id", "link", "_child_name",
                    'parentchildlinkextension_ptr'):
                d[field] = getattr(self, field)
        return d
    
def register_PCLE(PCLE):
    """
    Register *PCLE* so that openPLM can show its visible fields.

    :param PCLE: the registered PCLE
    :type PCLE: a subclass of :class:`ParentChildLinkExtension`.
    """
    registered_PCLEs.append(PCLE)

def get_PCLEs(parent):
    """
    Returns the list of registered :class:`ParentChildLinkExtension` that
    applied to *parent*.
    """
    return [PCLE for PCLE in registered_PCLEs if PCLE.apply_to(parent)]


class DocumentPartLink(Link):
    """
    Link between a :class:`Part` and a :class:`Document`
    
    :model attributes:
        .. attribute:: part

            a :class:`Part`
        .. attribute:: document

            a :class:`Document`
    """

    ACTION_NAME = "Link : document-part"

    document = models.ForeignKey(Document, related_name="%(class)s_document")    
    part = models.ForeignKey(Part, related_name="%(class)s_part")    

    class Meta:
        unique_together = ("document", "part")

    def __unicode__(self):
        return u"DocumentPartLink<%s, %s>" % (self.document, self.part)

# abstraction stuff
ROLE_NOTIFIED = "notified"
ROLE_SIGN = "sign_"
ROLE_OWNER = "owner"
ROLE_SPONSOR = "sponsor"

ROLES = [ROLE_OWNER, ROLE_NOTIFIED, ROLE_SPONSOR]
for i in range(10):
    level = level_to_sign_str(i)
    ROLES.append(level)

class DelegationLink(Link):
    """
    Link between two :class:`~.django.contrib.auth.models.User` to delegate
    his rights (abstract class)
    
    :model attributes:
        .. attribute:: delegator

            :class:`~django.contrib.auth.models.User` who gives his role
        .. attribute:: delegatee

            :class:`~django.contrib.auth.models.User` who receives the role
        .. attribute:: role
            
            right that is delegated
    """

    ACTION_NAME = "Link : delegation"
    
    delegator = models.ForeignKey(User, related_name="%(class)s_delegator")    
    delegatee = models.ForeignKey(User, related_name="%(class)s_delegatee")    
    role = models.CharField(max_length=30, choices=zip(ROLES, ROLES),
            db_index=True)

    class Meta:
        unique_together = ("delegator", "delegatee", "role")

    def __unicode__(self):
        return u"DelegationLink<%s, %s, %s>" % (self.delegator, self.delegatee,
                                                self.role)
    
    @classmethod
    def get_delegators(cls, user, role):
        """
        Returns the list of user's id of the delegators of *user* for the role
        *role*.
        """
        links = cls.objects.filter(role=role).values_list("delegatee", "delegator")
        gr = kjbuckets.kjGraph(tuple(links))
        return gr.reachable(user.id).items()


class PLMObjectUserLink(Link):
    """
    Link between a :class:`~.django.contrib.auth.models.User` and a
    :class:`PLMObject`
    
    :model attributes:
        .. attribute:: plmobject

            a :class:`PLMObject`
        .. attribute:: user

            a :class:`User`
        .. attribute:: role
            
            role of *user* for *plmobject* (like `owner` or `notified`)
    """

    ACTION_NAME = "Link : PLMObject-user"

    plmobject = models.ForeignKey(PLMObject, related_name="%(class)s_plmobject")    
    user = models.ForeignKey(User, related_name="%(class)s_user")    
    role = models.CharField(max_length=30, choices=zip(ROLES, ROLES),
            db_index=True)

    class Meta:
        unique_together = ("plmobject", "user", "role")
        ordering = ["user", "role", "plmobject__type", "plmobject__reference",
                "plmobject__revision"]

    def __unicode__(self):
        return u"PLMObjectUserLink<%s, %s, %s>" % (self.plmobject, self.user, self.role)


def _get_all_subclasses_with_level(base, lst, level):
    level = "=" + level
    if base.__name__ not in lst:
        lst.append((base.__name__,level[3:] + base.__name__))
    for part in base.__subclasses__():
        _get_all_subclasses_with_level(part, lst, level)

@memoize_noarg
def get_all_plmobjects_with_level():
    u"""
    Returns a list<name, class> of all available :class:`PLMObject` subclasses
    with 1 or more "=>" depending on the level
    """

    lst = []
    level=">"
    _get_all_subclasses_with_level(PLMObject, lst, level)
    if lst: del lst[0]
    lst.append(("Group", "Group"))
    return lst

@memoize_noarg
def get_all_users_and_plmobjects_with_level():
    list_of_choices = list(get_all_plmobjects_with_level())
    level=">"
    _get_all_subclasses_with_level(User, list_of_choices, level)
    return list_of_choices


class Invitation(models.Model):
    PENDING = "p"
    ACCEPTED = "a"
    REFUSED = "r"
    STATES = ((PENDING, "Pending"),
              (ACCEPTED, "Accepted"),
              (REFUSED, "Refused"))
    group = models.ForeignKey(GroupInfo)
    owner = models.ForeignKey(User, related_name="%(class)s_inv_owner")
    guest = models.ForeignKey(User, related_name="%(class)s_inv_guest")
    state = models.CharField(max_length=1, choices=STATES, default=PENDING)
    ctime = models.DateTimeField(_("date of creation"), default=datetime.datetime.today,
                                 auto_now_add=False)
    validation_time = models.DateTimeField(_("date of validation"), null=True)
    guest_asked = models.BooleanField(_("True if guest created the invitation"))
    token = models.CharField(max_length=155, primary_key=True,
            default=lambda:str(random.getrandbits(512)))
    
   
# import_models should be the last function

def import_models(force_reload=False):
    u"""
    Imports recursively all modules in directory *plmapp/customized_models*
    """

    MODELS_DIR = "customized_models"
    IMPORT_ROOT = "openPLM.plmapp.%s" % MODELS_DIR
    if __name__ != "openPLM.plmapp.models":
        # this avoids to import models twice
        return
    if force_reload or not hasattr(import_models, "done"):
        import_models.done = True
        models_dir = os.path.join(os.path.split(__file__)[0], MODELS_DIR)
        # we browse recursively models_dir
        for root, dirs, files in os.walk(models_dir):
            # we only look at python files
            for module in sorted(fnmatch.filter(files, "*.py")):
                if module == "__init__.py":
                    # these files are empty
                    continue
                # import_name should respect the format
                # 'openPLM.plmapp.customized_models.{module_name}'
                module_name = os.path.splitext(os.path.basename(module))[0]
                import_dir = root.split(MODELS_DIR, 1)[-1].replace(os.path.sep, ".")
                import_name = "%s.%s.%s" % (IMPORT_ROOT, import_dir, module_name)
                import_name = import_name.replace("..", ".")
                try:
                    __import__(import_name, globals(), locals(), [], -1)
                except ImportError, exc:
                    print "Exception in import_models", module_name, exc
                except StandardError, exc:
                    print "Exception in import_models", module_name, type(exc), exc
import_models()

