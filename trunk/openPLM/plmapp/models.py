#! -*- coding:utf-8 -*-

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
        - Delegation links:
            - :class:`AbstractDelegationLink`
            - :class:`DelegationLink`
            - :class:`ClosureDelegationLink`
            - :func:`add_transitive_links`
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
from django.db.models.signals import post_save
from django.conf import settings
from django.contrib.auth.models import User
from django.core.files.storage import FileSystemStorage
from django.utils.encoding import iri_to_uri
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop

from openPLM.plmapp.lifecycle import LifecycleList
from openPLM.plmapp.utils import level_to_sign_str


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
                "ctime", "mtime"]

    @property
    def menu_items(self):
        "menu items to choose a view"
        return ["attributes", "history", "parts-doc-cad", "delegation"]

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
    official_state = models.ForeignKey(State)

    # XXX description field ?

    def __unicode__(self):
        return u'Lifecycle<%s>' % self.name

    def to_states_list(self):
        u"""
        Converts a Lifecycle to a :class:`LifecycleList` (a list of strings)
        """
        
        lcs = LifecycleStates.objects.filter(lifecycle=self).order_by("rank")
        return LifecycleList(self.name, self.official_state.name,
                             *(l.state.name for l in lcs))

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

    .. note::
        This class is abstract, to create a PLMObject, see :class:`Part` and
        :class:`Document`.

    """

    # key attributes
    reference = models.CharField(_("reference"), max_length=50)
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

    def __unicode__(self):
        return u"%s<%s/%s/%s>" % (type(self).__name__, self.reference, self.type,
                                  self.revision)

    def _is_promotable(self):
        """
        Returns True if the object's state is the last state of its lifecyle
        """
        lcl = self.lifecycle.to_states_list()
        return lcl[-1] != self.state.name

    def is_promotable(self):
        u"""
        Returns True if object is promotable

        .. note::
            This method is abstract and raises :exc:`NotImplementedError`.
            This method must be overriden.
        """
        raise NotImplementedError()

    @property
    def is_editable(self):
        """
        True if the object is not in a non editable state
        (for example, in an official or deprecated state
        """
        current_rank = LifecycleStates.objects.get(state=self.state,
                            lifecycle=self.lifecycle).rank
        official_rank = LifecycleStates.objects.get(state=self.lifecycle.official_state,
                            lifecycle=self.lifecycle).rank
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
    def attributes(self):
        u"Attributes to display in `Attributes view`"
        return ["name",  "creator", "owner", "ctime", "mtime"]

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
        for field in cls().attributes:
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
        return ["creator", "owner", "ctime", "mtime"]

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
        Returns True if the object is promotable. A part is promotable
        if there is a next state in its lifecycle and if its childs which
        have the same lifecycle are in a state as mature as the object's state.  
        """
        if not self._is_promotable():
            return False
        childs = self.parentchildlink_parent.filter(end_time__exact=None).only("child")
        lcs = LifecycleStates.objects.filter(lifecycle=self.lifecycle)
        rank = lcs.get(state=self.state).rank
        for link in childs:
            child = link.child
            if child.lifecycle == self.lifecycle:
                rank_c = lcs.get(state=child.state).rank
                if rank_c < rank:
                    return False
        return True


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
class DocumentStorage(FileSystemStorage):
    """
    File system storage which stores files with a specific name
    """
    def get_available_name(self, name):
        """
        Returns a path for a file *name*, the path always refers to a file
        which do not exist.
        
        The path is computed as follow:
            #. a root directory: :const:`settings.DOCUMENTS_DIR`
            #. a directory which name is the last extension of *name*.
               For example, it is :file:`gz` if *name* is :file:`a.tar.gz`.
               If *name* does not have an extension, the directory is 
               :file:`no_ext/`.
            #. a file name with 4 parts:
                #. the md5 sum of *name*
                #. a dash separator: ``-``
                #. a random part with 3 characters in ``[a-z0-9]``
                #. the extension, like :file:`.gz`
            
            For example, if :const:`~settings.DOCUMENTS_DIR` is
            :file:`/var/openPLM/docs/`, and *name* is :file:`my_file.tar.gz`,
            a possible output is:

                :file:`/var/openPLM/docs/gz/c7bfe8d00ea6e7138215ebfafff187af-jj6.gz`

            If *name* is :file:`my_file`, a possible output is:

                :file:`/var/openPLM/docs/no_ext/59c211e8fc0f14b21c78c87eafe1ab72-dhh`
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
        path = os.path.join(settings.DOCUMENTS_DIR, ext2, md5_value % rand())
        while os.path.exists(path):
            path = os.path.join(settings.DOCUMENTS_DIR, ext2, md5_value % rand())
        return path

#: :class:`DocumentStorage` instance which stores files in :const:`settings.DOCUMENTS_DIR`
docfs = DocumentStorage(location=settings.DOCUMENTS_DIR)
#: :class:`FileSystemStorage` instance which stores thumbnails in :const:`settings.THUMBNAILS_DIR`
thumbnailfs = FileSystemStorage(location=settings.THUMBNAILS_DIR)

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
    file = models.FileField(upload_to="docs", storage=docfs)
    size = models.PositiveIntegerField()
    thumbnail = models.ImageField(upload_to="thumbnails", storage=thumbnailfs,
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
        return bool(self.files) and not bool(self.files.filter(locked=True))

    @property
    def menu_items(self):
        items = list(super(Document, self).menu_items)
        items.extend([ugettext_noop("parts"), ugettext_noop("files")])
        return items


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

def get_all_users_and_plmobjects():
    res = {}
    _get_all_subclasses(User, res)
    res.update(get_all_plmobjects())
    return res

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

class History(AbstractHistory):
    plmobject = models.ForeignKey(PLMObject)

class UserHistory(AbstractHistory):
    plmobject = models.ForeignKey(User)


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
        .. attribute:: order
            
            positive integer
        .. attribute:: end_time
            
            date of end of the link, None if the link is still alive
    """

    ACTION_NAME = "Link : parent-child"

    parent = models.ForeignKey(Part, related_name="%(class)s_parent")    
    child = models.ForeignKey(Part, related_name="%(class)s_child")    
    quantity = models.FloatField(default=lambda: 1)
    order = models.PositiveSmallIntegerField(default=lambda: 1)
    end_time = models.DateTimeField(blank=True, null=True, default=lambda: None)
    
    class Meta:
        unique_together = ("parent", "child", "end_time")

    def __unicode__(self):
        return u"ParentChildLink<%s, %s, %f, %d>" % (self.parent, self.child,
                                                     self.quantity, self.order)

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

ROLES = [("owner", "owner"),
         ("notified", "notified"),]
for i in range(10):
    level = level_to_sign_str(i)
    ROLES.append((level, level))

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
    role = models.CharField(max_length=30, choices=ROLES)

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
    role = models.CharField(max_length=30, choices=ROLES)

    class Meta:
        unique_together = ("plmobject", "user", "role")

    def __unicode__(self):
        return u"PLMObjectUserLink<%s, %s, %s>" % (self.plmobject, self.user, self.role)


def _get_all_subclasses_with_level(base, lst, level):
    level = "=" + level
    if base.__name__ not in lst:
        lst.append((base.__name__,level[3:] + base.__name__))
    for part in base.__subclasses__():
        _get_all_subclasses_with_level(part, lst, level)

def get_all_plmobjects_with_level():
    u"""
    Returns a list<name, class> of all available :class:`PLMObject` subclasses
    with 1 or more "=>" depending on the level
    """

    lst = []
    level=">"
    _get_all_subclasses_with_level(PLMObject, lst, level)
    if lst: del lst[0]
    return lst

def get_all_users_and_plmobjects_with_level():
    list_of_choices = get_all_plmobjects_with_level()
    level=">"
    _get_all_subclasses_with_level(User, list_of_choices, level)
    return list_of_choices

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

