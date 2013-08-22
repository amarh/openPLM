from itertools import chain
import datetime
from django.utils import timezone

from django.conf import settings
from django.db import models
from django.db.models.query import QuerySet
from django.contrib.auth.models import User, Group
from django.contrib.comments.signals import comment_was_posted
from django.utils.translation import ugettext_lazy as _

from .lifecycle import State, Lifecycle, get_cancelled_state
from .plmobject import PLMObject
from .part import get_all_parts
from .document import get_all_documents

def _prefetch_related(qs, *extra):
    return qs.prefetch_related("plmobject", "user", "user__profile", *extra)

# history stuff
class AbstractHistory(models.Model):
    u"""
    History model.
    This model records all events related to :class:`.PLMObject`

    :model attributes:
        .. attribute:: plmobject

            :class:`.PLMObject` of the event
        .. attribute:: action

            type of action (see :attr:`.ACTIONS`)
        .. attribute:: details

            type of action (see :attr:`.ACTIONS`)
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
        ("Cancel", "Cancel"),
        ("Publish", "Publish"),
        ("Unpublish", "Unpublish"),
    )

    class Meta:
        abstract = True

    action = models.CharField(max_length=50, choices=ACTIONS)
    details = models.TextField()
    date = models.DateTimeField(auto_now=True)
    user = models.ForeignKey(User, related_name="%(class)s_user")

    def __unicode__(self):
        return "History<%s, %s, %s>" % (self.plmobject, self.date, self.action)

    def get_day_as_int(self):
        return self.date.year * 10000 + self.date.month * 100 + self.date.day

    def get_day(self):
        return datetime.date(self.date.year, self.date.month, self.date.day)

    @classmethod
    def timeline_items(cls, user):
        return _prefetch_related(cls.objects.all().order_by("-date"))

    @property
    def title(self):
        return self.plmobject.title


class History(AbstractHistory):
    class Meta:
        app_label = "plmapp"
    plmobject = models.ForeignKey(PLMObject)

    def get_redirect_url(self):
        return "/history_item/object/%d/" % self.id

    @classmethod
    def timeline_items(cls, user):
        q = models.Q(plmobject__owner__username=settings.COMPANY)
        q |= models.Q(plmobject__group__in=user.groups.all())
        histories = History.objects.filter(q).order_by('-date')
        return _prefetch_related(histories)

class UserHistory(AbstractHistory):
    class Meta:
        app_label = "plmapp"
    plmobject = models.ForeignKey(User)

    def get_redirect_url(self):
        return "/history_item/user/%d/" % self.id

    @property
    def title(self):
        return self.plmobject.username

    @classmethod
    def timeline_items(cls, user):
        return _prefetch_related(cls.objects.all().order_by("-date"))


class GroupHistory(AbstractHistory):
    class Meta:
        app_label = "plmapp"
    plmobject = models.ForeignKey(Group)

    def get_redirect_url(self):
        return "/history_item/group/%d/" % self.id

    @classmethod
    def timeline_items(cls, user):
        return _prefetch_related(cls.objects.all().order_by("-date"), "plmobject__groupinfo")

    @property
    def title(self):
        return self.plmobject.groupinfo.title


class StateHistoryQuerySet(QuerySet):
    """ QuerySet with utility methods to filter :class:`StateHistory` alive at a given time."""

    def now(self):
        """
        Filters state histories: keeps only alive state histories (end_time is null).
        """
        return self.filter(end_time__isnull=True)

    def at(self, time):
        """
        Filters state histories: keeps alive state histories at time *time*.

        :param time: a :class:`~datetime.datetime` or None
        """
        if time is None:
            return self.now()
        return self.filter(start_time__lte=time).exclude(end_time__lt=time)

    def officials(self):
        """
        Filters only official state histories.
        """
        return self.filter(state_category=StateHistory.OFFICIAL)


class StateHistoryManager(models.Manager):
    """state histories manager, returns a :class:`StateHistoryQuerySet`."""

    use_for_related_fields = True

    def get_query_set(self):
        return StateHistoryQuerySet(self.model)

    def now(self):
        """
        Shorcut for ``self.get_query_set().now()``. See :meth:`StateHistoryQuerySet.now`.
        """
        return self.get_query_set().now()

    def at(self, time):
        """
        Shorcut for ``self.get_query_set().at(time)``. See :meth:`StateHistoryQuerySet.at`.
        """
        return self.get_query_set().at(time)

    def officials(self):
        """
        Shorcut for ``self.get_query_set().officials()``. See :meth:`StateHistoryQuerySet.officials()`.
        """
        return self.get_query_set().officials()


class StateHistory(models.Model):
    """
    Models that tracks the promotions and demotions of a :class:`.PLMObject`.

    :model attributes:
        .. attribute:: plmobject

            :class:`.PLMObject` that has been promoted/demoted.
        .. attribute:: start_time

            date of the promotion/demotion
        .. attribute:: end_time

            date of the next promotion/demotion, None if the promotion
            is the latest promotion
        .. attribute:: state

            :class:`.State` of *plmobject* at *t*, if *start_time* <= t < *end_time*
        .. attribute:: lifecycle

            :class:`.Lifecycle` of *plmobject* at *t*, if *start_time* <= t < *end_time*
        .. attribute:: state_category

            state's category of *plmobject* at *t*, if *start_time* <= t < *end_time*.
            This field is redundant with the tuple (state, lifecycle) but it allows
            fast queries to check if an object was official at a given time.
            This attribute is automatically set when the object is saved.

        Valid state's categories are:

            .. attribute:: DRAFT

                set if :meth:`.PLMObject.is_draft` returns True
            .. attribute:: PROPOSED

                set if :meth:`.PLMObject.is_proposed` returns True
            .. attribute:: OFFICIAL

                set if :meth:`.PLMObject.is_official` returns True
            .. attribute:: DEPRECATED

                set if :meth:`.PLMObject.is_deprecated` returns True
            .. attribute:: CANCELLED

                set if :meth:`.PLMObject.is_cancelled` returns True

    """

    class Meta:
        app_label = "plmapp"

    DRAFT, PROPOSED, OFFICIAL, DEPRECATED, CANCELLED = range(5)
    STATE_CATEGORIES = (
        (DRAFT, "draft"),
        (PROPOSED, "proposed"),
        (OFFICIAL, "official"),
        (DEPRECATED, "deprecated"),
        (CANCELLED, "cancelled")
    )

    plmobject = models.ForeignKey(PLMObject)
    state = models.ForeignKey(State)
    lifecycle = models.ForeignKey(Lifecycle)
    start_time = models.DateTimeField(_("date of promotion"),
            default=timezone.now, auto_now_add=False)
    end_time = models.DateTimeField(null=True)
    state_category = models.PositiveSmallIntegerField(choices=STATE_CATEGORIES)

    objects = StateHistoryManager()

    def save(self, *args, **kwargs):
        if self.state == get_cancelled_state():
            category = StateHistory.CANCELLED
        elif self.state == self.lifecycle.official_state:
            category = StateHistory.OFFICIAL
        elif self.state == self.lifecycle.first_state:
            category = StateHistory.DRAFT
        elif self.state == self.lifecycle.last_state:
            category = StateHistory.DEPRECATED
        else:
            category = StateHistory.PROPOSED
        self.state_category = category
        super(StateHistory, self).save(*args, **kwargs)

def timeline_histories(user, date_begin=None, date_end=None, done_by=None, list_display=None):
    if date_begin is None and date_end is None:
        return History.timeline_items(user)
    else:
        history = None
        history_plmobject = None
        history_group = None

        if list_display["display_document"] or list_display["display_part"]:
            history_plmobject = History.timeline_items(user)
            if list_display["display_document"] and not list_display["display_part"]:
                documents = get_all_documents().keys()
                history_plmobject = history_plmobject.filter(plmobject__type__in = documents)
            elif not list_display["display_document"]:
                parts = get_all_parts().keys()
                history_plmobject = history_plmobject.filter(plmobject__type__in = parts)
            history_plmobject = history_plmobject.filter(date__gte = date_end, date__lt = date_begin)

            if done_by:
                if User.objects.filter(username=done_by).exists():
                    history_plmobject = history_plmobject.filter(user__username = done_by)
                else:
                    history_plmobject = history_plmobject.none()

        if list_display["display_group"]:
            history_group = GroupHistory.timeline_items(user)
            history_group = history_group.filter(date__gte = date_end, date__lt = date_begin)

            if done_by != "":
                if User.objects.filter(username= done_by).exists():
                    history_group = history_group.filter(user__username = done_by)
                else:
                    history_group = history_group.none()
            for h in history_group:
                h.plmobject.plmobject_url = h.plmobject.groupinfo.plmobject_url

        if (list_display["display_document"] or list_display["display_part"]) and list_display["display_group"]:
            history = sorted(chain(history_group, history_plmobject), key=lambda instance: instance.date, reverse=True)
        elif list_display["display_group"]:
            history = history_group
        elif list_display["display_document"] or list_display["display_part"]:
            history = history_plmobject

        return history


def _save_comment_history(sender, comment, request, **kwargs):
    """
    Save an history line when a comment is posted.
    """
    from openPLM.plmapp.controllers import get_controller
    obj = comment.content_object
    ctrl_cls = get_controller(obj.__class__.__name__)
    ctrl = ctrl_cls(comment.content_object, request.user, no_index=True)
    ctrl._save_histo("New comment", comment.comment)

comment_was_posted.connect(_save_comment_history)

