from django.utils import timezone
import kjbuckets


from django.core.exceptions import ValidationError
from django.db import models, IntegrityError
from django.db.models.query import QuerySet
from django.contrib.auth.models import User

from openPLM.plmapp.utils.units import UNITS, DEFAULT_UNIT
from openPLM.plmapp.utils import level_to_sign_str

from .lifecycle import State
from .plmobject import PLMObject
from .part import Part
from .document import Document

class LinkQuerySet(QuerySet):
    """ QuerySet with utility methods to filter links alive at a given time."""

    def now(self):
        """
        Filters links: keeps only alive links (end_time is null).
        """
        return self.filter(end_time__isnull=True)

    def at(self, time):
        """
        Filters links: keeps alive links at time *time*.

        :param time: a :class:`~datetime.datetime` or None
        """
        if time is None:
            return self.now()
        return self.filter(ctime__lte=time).exclude(end_time__isnull=False,
                end_time__lt=time)

    def end(self):
        """
        Ends all alive links: sets theur :attr:`end_time` to the current time and saves them
        if there :attr:`end_time` are not already set.
        """
        return self.now().update(end_time=timezone.now())


class LinkManager(models.Manager):
    """Links manager, returns a :class:`LinkQuerySet`."""

    use_for_related_fields = True

    def get_query_set(self):
        return LinkQuerySet(self.model)

    def now(self):
        """
        Shorcut for ``self.get_query_set().now()``. See :meth:`LinkQuerySet.now`.
        """
        return self.get_query_set().now()

    def at(self, time):
        """
        Shorcut for ``self.get_query_set().at(time)``. See :meth:`LinkQuerySet.at`.
        """
        return self.get_query_set().at(time)

    def end(self):
        """
        Shorcut for ``self.get_query_set().end()``. See :meth:`LinkQuerySet.end`.
        """
        return self.get_query_set().end()


class CurrentLinkManager(LinkManager):
    """
    Manager which returns alive links.
    """

    def get_query_set(self):
        return LinkQuerySet(self.model).now()


class Link(models.Model):
    u"""
    Abstract link base class.

    This class represents a link between two :class:`.PLMObject`

    :model attributes:
        .. attribute:: ctime

            date of creation of the link (automatically set)
        .. attribute:: end_time

            date of deletion of the link (default: None, the link is still active)

    :class attributes:
        .. attribute:: ACTION_NAME

            an identifier used to set :attr:`.History.action` field
        .. attribute:: objects

            default manager: instance of :class:`LinkManager`

        .. attribute:: current_objects

            alternate manager (:class:`CurrentLinkManager`) which returns alive links.
    """

    ctime = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(blank=True, null=True, default=lambda: None)

    objects = LinkManager()
    current_objects = CurrentLinkManager()

    ACTION_NAME = "Link"

    class Meta:
        abstract = True

    def clean(self):
        """
        Check for instances with null values in unique_together fields.
        """
        super(Link, self).clean()

        for field_tuple in self._meta.unique_together[:]:
            unique_filter = {}
            unique_fields = []
            null_found = False
            for field_name in field_tuple:
                field_value = getattr(self, field_name)
                if getattr(self, field_name) is None:
                    unique_filter['%s__isnull'%field_name] = True
                    null_found = True
                else:
                    unique_filter['%s'%field_name] = field_value
                    unique_fields.append(field_name)
            if null_found:
                unique_queryset = self.__class__.objects.filter(**unique_filter)
                if self.pk:
                    unique_queryset = unique_queryset.exclude(pk=self.pk)
                if unique_queryset.exists():
                    msg = self.unique_error_message(self.__class__, tuple(unique_fields))
                    raise ValidationError(msg)

    def save(self, *args, **kwargs):
        if self.pk is None and self.end_time is None:
            try:
                self.clean()
            except ValidationError as e:
                raise IntegrityError(e)
        super(Link, self).save(*args, **kwargs)

    def end(self):
        """
        Ends the link: sets its :attr:`end_time` to the current time and saves it
        if its :attr:`end_time` is not already set.
        """
        if self.end_time is None:
            self.end_time = timezone.now()
            self.save()

class ParentChildLink(Link):
    """
    Link between two :class:`.Part`: a parent and a child

    :model attributes:
        .. attribute:: parent

            a :class:`.Part`
        .. attribute:: child

            a :class:`.Part`
        .. attribute:: quantity

            amount of child (a positive float)
        .. attribute:: unit

            unit of the quantity
        .. attribute:: order

            positive integer

    """

    ACTION_NAME = "Link : parent-child"

    parent = models.ForeignKey(Part, related_name="%(class)s_parent")
    child = models.ForeignKey(Part, related_name="%(class)s_child")
    quantity = models.FloatField(default=lambda: 1)
    unit = models.CharField(max_length=4, choices=UNITS,
            default=lambda: DEFAULT_UNIT)
    order = models.PositiveSmallIntegerField(default=lambda: 1)

    class Meta:
        app_label = "plmapp"
        unique_together = ("parent", "child", "end_time")

    def __unicode__(self):
        return u"ParentChildLink<%s, %s, %f, %s, %d>" % (self.parent, self.child,
                                 self.quantity, self.unit, self.order)

    def get_shortened_unit(self):
        """ Returns unit as a human readable string.
        If :attr:`.unit` equals to "-", returns an empty string.
        """
        if self.unit == "-":
            return u""
        return self.get_unit_display()

    @property
    def extensions(self):
        """ Returns a queryset of bound :class:`.ParentChildLinkExtension`. """
        return ParentChildLinkExtension.children.filter(link=self)

    def get_extension_data(self):
        """
        Returns a dictionary of extension data. The returned value can be passed
        as a valid arguement to :meth:`.clone`.
        """

        extension_data = {}
        for ext in self.extensions:
            if ext.one_per_link():
                extension_data[ext._meta.module_name] = ext.to_dict()
        return extension_data

    def clone(self, save=False, extension_data=None, **kwargs):
        u"""
        Clone this link.

        It is possible to pass additional arguments to override some original
        values.

        :param save: If True, the cloned link and its extensions are saved
        :param extension_data: dictionary PCLE module name -> data of data
            that are given to :meth:`.ParentChildLinkExtension.clone`.

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
    Extension of a :class:`.ParentChildLink` used to store additional data.

    This class is abstract, subclass must define the :meth:`.clone` method,
    add at least one field (or it would be useless) and may override
    :meth:`.get_visible_fields` or :meth:`.get_editable_fields`.

    .. seealso::

        :ref:`bom_extensions` explains how to subclass this class.
    """

    class Meta:
        app_label = "plmapp"

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

        By default, returns :meth:`.get_visible_fields`.
        """
        return list(cls.get_visible_fields())

    @classmethod
    def one_per_link(cls):
        """ Returns True if only one extension should be created per link.

        By default return True if :meth:`.get_visible_fields` returns a
        non empty list."""
        return bool(cls.get_visible_fields())

    @classmethod
    def apply_to(cls, parent):
        """
        Returns True if this extension applies to *parent*.

        :param parent: part which will have a new child
        :type parent: :class:`.Part` (its most specific subclass).

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
        :type link: :class:`.ParentChildLink`
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
        a kwargument to :meth:`.clone` and that is used to compare two
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
    :type PCLE: a subclass of :class:`.ParentChildLinkExtension`.
    """
    registered_PCLEs.append(PCLE)

def get_PCLEs(parent):
    """
    Returns the list of registered :class:`.ParentChildLinkExtension` that
    applied to *parent*.
    """
    return [PCLE for PCLE in registered_PCLEs if PCLE.apply_to(parent)]


class RevisionLink(Link):
    """
    Link between two revisions of a :class:`.PLMObject`

    :model attributes:
        .. attribute:: old

            old revision (a :class:`.PLMObject`)
        .. attribute:: new

            new revision (a :class:`.PLMObject`)
    """

    class Meta:
        app_label = "plmapp"
        unique_together = ("old", "new", "end_time")

    ACTION_NAME = "Link : revision"
    old = models.ForeignKey(PLMObject, related_name="%(class)s_old")
    new = models.ForeignKey(PLMObject, related_name="%(class)s_new")

    def __unicode__(self):
        return u"RevisionLink<%s, %s>" % (self.old, self.new)

class DocumentPartLink(Link):
    """
    Link between a :class:`.Part` and a :class:`.Document`

    :model attributes:
        .. attribute:: part

            a :class:`.Part`
        .. attribute:: document

            a :class:`.Document`
    """

    ACTION_NAME = "Link : document-part"

    document = models.ForeignKey(Document, related_name="%(class)s_document")
    part = models.ForeignKey(Part, related_name="%(class)s_part")

    class Meta:
        app_label = "plmapp"
        unique_together = ("document", "part", "end_time")

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
ROLE_READER = "reader"
ROLES.append(ROLE_READER)

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
        app_label = "plmapp"
        unique_together = ("delegator", "delegatee", "role", "end_time")

    def __unicode__(self):
        return u"DelegationLink<%s, %s, %s>" % (self.delegator, self.delegatee,
                                                self.role)

    @classmethod
    def get_delegators(cls, user, role):
        """
        Returns the list of user's id of the delegators of *user* for the role
        *role*.
        """
        links = cls.current_objects.filter(role=role).values_list("delegatee", "delegator")
        gr = kjbuckets.kjGraph(tuple(links))
        return gr.reachable(user.id).items()


class PLMObjectUserLink(Link):
    """
    Link between a :class:`~.django.contrib.auth.models.User` and a
    :class:`.PLMObject`

    :model attributes:
        .. attribute:: plmobject

            a :class:`.PLMObject`
        .. attribute:: user

            a :class:`.User`
        .. attribute:: role

            role of *user* for *plmobject* (like `owner` or `notified`)
    """

    ACTION_NAME = "Link : PLMObject-user"

    plmobject = models.ForeignKey(PLMObject, related_name="users")
    user = models.ForeignKey(User, related_name="%(class)s_user")
    role = models.CharField(max_length=30, choices=zip(ROLES, ROLES),
            db_index=True)

    class Meta:
        app_label = "plmapp"
        unique_together = ("plmobject", "user", "role", "end_time")
        ordering = ["user", "role", "plmobject__type", "plmobject__reference",
                "plmobject__revision"]

    def __unicode__(self):
        return u"PLMObjectUserLink<%s, %s, %s>" % (self.plmobject, self.user, self.role)


class PromotionApproval(Link):
    """
    .. versionadded:: 1.2

    Model to track a promotion approval

    :model attributes:
        .. attribute:: plmobject

            approved :class:`.PLMObject`
        .. attribute:: user

            :class:`.User` who approved the promotion
        .. attribute:: current_state

            current :class:`.State` of :attr:`plmobject`
        .. attribute:: next_state

            next :class:`.State` of :attr:`plmobject` when if will be promoted

    """
    plmobject = models.ForeignKey(PLMObject, related_name="approvals")
    user = models.ForeignKey(User, related_name="approvals")
    current_state = models.ForeignKey(State, related_name="+")
    next_state = models.ForeignKey(State, related_name="+")

    class Meta:
        app_label = "plmapp"
        unique_together = ("plmobject", "user", "current_state", "next_state", "end_time")

class PartSet(Link):

    parts = models.ManyToManyField(Part, related_name="%(class)ss")

    class Meta:
        app_label = "plmapp"
        abstract = True

    def add_part(self, part):
        new_partset = self.__class__.objects.create()
        new_partset.parts.add(part, *self.parts.all())
        self.end()
        return new_partset

    def remove_part(self, part):
        if self.parts.all().count() == 2:
            self.end()
            return None
        else:
            new_partset = self.__class__.objects.create()
            new_partset.parts.add(*[p for p in self.parts.all() if p.id != part.id])
            self.end()
            return new_partset

    @classmethod
    def join(cls, part, part_or_set):
        if isinstance(part_or_set, cls):
            return part_or_set.add_part(part)
        partset = cls.get_partset(part_or_set)
        if partset is None:
            partset = cls.get_partset(part)
            if partset is not None:
                return partset.add_part(part_or_set)
            new_partset = cls.objects.create()
            new_partset.parts.add(part, part_or_set)
            return new_partset
        else:
            return partset.add_part(part)

    @classmethod
    def get_partset(cls, part):
        try:
           partset = getattr(part, "%ss" % cls.__name__.lower()).now().get()
           return partset
        except cls.DoesNotExist:
            return None

    @classmethod
    def get_related_parts(cls, parts):
        if not parts:
            return []
        ps = cls.objects.now().filter(parts__in=parts).distinct()
        query = {"%ss__in" % cls.__name__.lower() : ps}
        return list(set(Part.objects.filter(**query).values_list("id", flat=True)))


class AlternatePartSet(PartSet):

    class Meta:
        app_label = "plmapp"


