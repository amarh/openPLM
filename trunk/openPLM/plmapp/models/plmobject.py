
from functools import wraps

from django.db import models
from django.db.models import F
from django.db.models.query import QuerySet
from django.forms.util import ErrorList
from django.contrib.auth.models import User
from django.utils.encoding import iri_to_uri
from django.utils.html import conditional_escape as esc
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.utils.translation import ugettext_noop, ugettext_lazy as _

from openPLM.plmapp.utils import level_to_sign_str, memoize_noarg
from .iobject import IObject
from .lifecycle import (State, Lifecycle, LifecycleStates,
        get_default_lifecycle, get_default_state, get_cancelled_lifecycle)
from .group import GroupInfo


# PLMobjects
def cache_lifecycle_stuff(func):
    """
    A decorator that caches the result of *func*.

    *func* must take one argument: a :class:`.PLMObject` and
    its returned value should only depends on the state and the
    lifecycle of the given PLMObject (and not its type).

    The maximum cache size will be the number of
    :class:`.LifecycleStates`. Each key of the cache is
    a tuple (state's name, lifecycle's name).
    """
    @wraps(func)
    def wrapper(plmobject):
        key = (plmobject.state_id, plmobject.lifecycle_id)
        if key in func.cache:
            return func.cache[key]
        else:
            value = func(plmobject)
            func.cache[key] = value
            return value
    func.cache = {}
    wrapper.__doc__ += """

        .. note::

            The result of this function is cached with :func:`._cache_lifecycle_stuff`.
    """
    return wrapper


class PLMObjectQuerySet(QuerySet):
    """
    A :class:`QuerySet` with extra methods to filter results by their state.
    """

    def officials(self):
        """ Retrieves only official :class:`PLMObject`. """
        return self.filter(state=F("lifecycle__official_state"))

    def exclude_cancelled(self):
        """ Excludes cancelled :class:`PLMObject`. """
        return self.exclude(lifecycle=get_cancelled_lifecycle())


class PLMObjectManager(models.Manager):
    """ Manager for :class:`PLMObject`.
    Uses a :class:`PLMObjectQuerySet`."""

    use_for_related_fields = True

    def get_query_set(self):
        return PLMObjectQuerySet(self.model)

    def officials(self):
        """ Retrieves only official :class:`PLMObject`. """
        return self.get_query_set().officials()

    def exclude_cancelled(self):
        """ Excludes cancelled :class:`PLMObject`. """
        return self.get_query_set().exclude_cancelled()


class AbstractPLMObject(models.Model):
    """
    Abstract model that redefines the :attr:`PLMObject.objects` manager.

    This model is abstract so that child classes inherits
    the manager.
    """

    class Meta:
        abstract = True

    objects = PLMObjectManager()


class PLMObject(AbstractPLMObject):
    u"""
    Base class for :class:`.Part` and :class:`.Document`.

    A PLMObject is identified by a triplet reference/type/revision

    :key attributes:
        .. attribute:: reference

            Reference of the :class:`.PLMObject`, for example ``YLTG00``
        .. attribute:: type

            Type of the :class:`.PLMObject`, for example ``Game``
        .. attribute:: revision

            Revision of the :class:`.PLMObject`, for example ``a``

    :other attributes:
        .. attribute:: name

            Name of the product, for example ``Game of life``
        .. attribute:: creator

            :class:`~django.contrib.auth.models.User` who created the :class:`.PLMObject`
        .. attribute:: creator

            :class:`~django.contrib.auth.models.User` who owns the :class:`.PLMObject`
        .. attribute:: ctime

            date of creation of the object (default value : current time)
        .. attribute:: mtime

            date of last modification of the object (automatically field at each save)
        .. attribute:: lifecycle

            :class:`.Lifecycle` of the object
        .. attribute:: state

            Current :class:`.State` of the object
        .. attribute:: group

            :class:`.GroupInfo` that owns the object
        .. attribute:: published

            .. versionadded:: 1.1

            True if the object is published (accessible to anonymous user)
        .. attribute:: reference_number

            .. versionadded:: 1.1

            number found in the reference if it matches ``PART_|DOC_\d+``

        .. attribute:: description

            .. versionadded:: 2.0

            a short description of the object. This field is optional
            and is a richtext field.

    .. note::

        This class is abstract, to create a PLMObject, see :class:`.Part` and
        :class:`.Document`.

    .. versionchanged:: 1.1
        :attr:`.published` and :attr:`.reference_number` added.
    """

    # key attributes
    reference = models.CharField(_("reference"), max_length=50, db_index=True,
                                 help_text=_(u"Required. 50 characters or fewer. Letters, numbers , except #, ?, / and .. characters"))
    type = models.CharField(_("type"), max_length=50)
    revision = models.CharField(_("revision"), max_length=50)

    # hidden field to get a valid new reference
    reference_number = models.IntegerField(default=0)

    # other attributes
    name = models.CharField(_("name"), max_length=100, blank=True,
                            help_text=_(u"Name of the product"))

    description = models.TextField(_("description"), blank=True, default="")
    description.richtext = True

    creator = models.ForeignKey(User, verbose_name=_("creator"),
                                related_name="%(class)s_creator")
    owner = models.ForeignKey(User, verbose_name=_("owner"),
                              related_name="%(class)s_owner")
    ctime = models.DateTimeField(_("date of creation"), default=timezone.now,
                                 auto_now_add=False)
    mtime = models.DateTimeField(_("date of last modification"), auto_now=True)
    group = models.ForeignKey(GroupInfo, verbose_name=_("group"), related_name="%(class)s_group")

    # state and lifecycle
    lifecycle = models.ForeignKey(Lifecycle, verbose_name=_("lifecycle"),
                                  related_name="+",
                                  default=get_default_lifecycle)
    state = models.ForeignKey(State, verbose_name=_("state"),
                              related_name="+",
                              default=get_default_state)

    published = models.BooleanField(verbose_name=_("published"), default=False)

    class Meta:
        # keys in the database
        app_label = "plmapp"
        unique_together = (('reference', 'type', 'revision'),)
        ordering = ["type", "reference", "revision"]

    def __init__(self, *args, **kwargs):
        # little hack:
        # get_creation_fields is a class method but it needs to create
        # an instance, this hack avoids calls to default value functions
        if "__fake__" not in kwargs:
            super(PLMObject, self).__init__(*args, **kwargs)
        self._promotion_errors = None
        self._title = None
        self._plmobject_url = None

    def __unicode__(self):
        return u"%s<%s/%s/%s>" % (type(self).__name__, self.reference, self.type,
                                  self.revision)

    @property
    def title(self):
        if self._title is None:
            attrs = tuple(esc(x) for x in [self.name, self.type, self.reference, self.revision])
            self._title = mark_safe(u'''<span class="name">%s</span> (<span class="type">%s</span> // <span class="reference">%s</span>
 // <span class="revision">%s</span>)''' % attrs)
        return self._title

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
            This method is abstract and raises :exc:`.NotImplementedError`.
            This method must be overriden.
        """
        raise NotImplementedError()

    def _get_promotion_errors(self):
        """ Returns an :class:`.ErrorList` of promotion errors.
        Calls :meth:`.is_promotable()` if it has not already been called.
        """
        if self._promotion_errors is None:
            self.is_promotable()
        return self._promotion_errors
    promotion_errors = property(_get_promotion_errors)

    @property
    def is_cloneable(self):
        """
        .. versionadded:: 1.1

        Return true by default. This property may be overriden
        by custom Part or Document
        """
        return True


    @property
    def is_editable(self):
        """
        True if the object is not in a non editable state
        """
        return self.is_draft and not self.approvals.now().exists()

    @property
    @cache_lifecycle_stuff
    def is_proposed(self):
        """
        True if the object is in a state prior to the official state
        but not draft.
        """
        if self.is_cancelled or self.is_draft:
            return False
        lcs = self.lifecycle.lifecyclestates_set.only("rank")
        current_rank = lcs.get(state=self.state).rank
        official_rank = lcs.get(state=self.lifecycle.official_state).rank
        return current_rank < official_rank

    @property
    @cache_lifecycle_stuff
    def is_cancelled(self):
        """ True if the object is cancelled. """
        return self.lifecycle == get_cancelled_lifecycle()

    @property
    @cache_lifecycle_stuff
    def is_deprecated(self):
        """ True if the object is deprecated. """
        return not self.is_cancelled and self.state == self.lifecycle.last_state

    @property
    @cache_lifecycle_stuff
    def is_official(self):
        u"Returns True if object is official."""
        return not self.is_cancelled and self.state == self.lifecycle.official_state

    @property
    @cache_lifecycle_stuff
    def is_draft(self):
        u""" Returns True if the object is a draft. """
        return not self.is_cancelled and self.state == self.lifecycle.first_state

    @cache_lifecycle_stuff
    def get_current_sign_level(self):
        """
        Returns the current sign level that a user must have to promote this
        object.
        """
        rank = LifecycleStates.objects.get(state=self.state,
                            lifecycle=self.lifecycle).rank
        return level_to_sign_str(rank)

    @cache_lifecycle_stuff
    def get_previous_sign_level(self):
        """
        Returns the current sign level that a user must have to demote this
        object.
        """
        rank = LifecycleStates.objects.get(state=self.state,
                            lifecycle=self.lifecycle).rank
        return level_to_sign_str(rank - 1)

    @property
    def is_part(self):
        """ True if the plmobject is a part."""
        from openPLM.plmapp.models.part import Part
        if self.type in get_all_plmobjects():
            return issubclass(get_all_plmobjects()[self.type], Part)
        return False

    @property
    def is_document(self):
        """ True if the plmobject is a document."""
        from openPLM.plmapp.models.document import Document
        if self.type in get_all_plmobjects():
            return issubclass(get_all_plmobjects()[self.type], Document)
        return False

    @property
    def attributes(self):
        u"Attributes to display in `Attributes view`"
        return ["type", "reference", "revision", "name", "description",
                "creator", "owner", "group", "ctime", "mtime"]

    @property
    def published_attributes(self):
        u""".. versionadded:: 1.1

        Attributes that are visible to everyone if the object has been published."""
        return ["type", "reference", "revision", "name",]

    @property
    def menu_items(self):
        "Menu items to choose a view"
        return [ugettext_noop("attributes"), ugettext_noop("lifecycle"),
                ugettext_noop("revisions"), ugettext_noop("history"),
               ]

    @classmethod
    def excluded_creation_fields(cls):
        "Returns fields which should not be available in a creation form"
        return ["owner", "creator", "ctime", "mtime", "state"]

    @property
    def plmobject_url(self):
        if self._plmobject_url is None:
            url = u"/object/%s/%s/%s/" % (self.type, self.reference, self.revision)
            self._plmobject_url = iri_to_uri(url)
        return self._plmobject_url

    @classmethod
    def get_creation_fields(cls):
        """
        Returns fields which should be displayed in a creation form.

        By default, it returns :attr:`.attributes` less attributes returned by
        :meth:`.excluded_creation_fields`
        """
        fields = ["name", "group", "reference", "type", "revision", "lifecycle", "description"]
        excludes = cls.excluded_creation_fields()
        for field in cls(__fake__=True).attributes:
            if field not in excludes and field not in fields:
                fields.insert(2, field)
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

        By default, it returns :attr:`.attributes` less attributes returned by
        :meth:`.excluded_modification_fields`
        """
        fields = []
        for field in cls(__fake__=True).attributes:
            if field not in cls.excluded_modification_fields():
                fields.append(field)
        return fields

    def get_leaf_object(self):
        return get_all_plmobjects()[self.type].objects.get(id=self.id)

    def get_current_signer_role(self):
        lcl = self.lifecycle.to_states_list()
        return level_to_sign_str(lcl.index(self.state.name))

    def get_current_signers(self):
        role = self.get_current_signer_role()
        return self.users.now().filter(role=role).values_list("user", flat=True)

    def get_approvers(self):
        if self.is_deprecated or self.is_cancelled:
            return self.approvals.none()
        lcl = self.lifecycle.to_states_list()
        next_state = lcl.next_state(self.state.name)
        approvers = self.approvals.now().filter(current_state=self.state,
                next_state=next_state).values_list("user", flat=True)
        return approvers


def get_all_subclasses(base, d):
    if base.__name__ not in d and not getattr(base, "_deferred", False):
        d[base.__name__] = base
    for cls in base.__subclasses__():
        get_all_subclasses(cls, d)


@memoize_noarg
def get_all_plmobjects():
    u"""
    Returns a dict<name, class> of all available :class:`.PLMObject` subclasses
    """
    res = {}
    get_all_subclasses(PLMObject, res)
    res["Group"] = GroupInfo
    del res["PLMObject"]
    get_all_subclasses(IObject, res)
    del res["IObject"]
    return res

@memoize_noarg
def get_all_users_and_plmobjects():
    res = {}
    get_all_subclasses(User, res)
    get_all_subclasses(IObject, res)
    del res["IObject"]
    res.update(get_all_plmobjects())
    return res


def get_all_subclasses_with_level(base, lst, level):
    level = "=" + level
    if base.__name__ not in lst:
        lst.append((base.__name__,level[3:] + base.__name__))
    subclasses = base.__subclasses__()
    subclasses.sort(key=lambda c: c.__name__)
    for cls in subclasses:
        if not getattr(cls, "_deferred", False):
            get_all_subclasses_with_level(cls, lst, level)


def get_subclasses(base):
    r = []
    def populate(b, l):
        r.append((l, b, b.__name__))
        subclasses = b.__subclasses__()
        subclasses.sort(key=lambda c: c.__name__)
        for cls in subclasses:
            if not getattr(cls, "_deferred", False):
                populate(cls, l + 1)
    populate(base, 0)
    return r

@memoize_noarg
def get_all_users_and_plmobjects_with_level():
    choices = []
    get_all_subclasses_with_level(PLMObject, choices, ">")
    del choices[0]
    ichoices = []
    get_all_subclasses_with_level(IObject, ichoices, ">")
    del ichoices[0]
    choices.extend(ichoices)
    choices.append(("Group", "Group"))
    choices.append(("User", "User"))
    return choices



