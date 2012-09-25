
import datetime

from django.db import models
from django.db.models.query import QuerySet
from django.contrib.auth.models import User, Group
from django.utils.translation import ugettext_lazy as _

from .lifecycle import State, Lifecycle, get_cancelled_state
from .plmobject import PLMObject

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

    def get_day(self):
        return datetime.date(self.date.year, self.date.month, self.date.day) 


class History(AbstractHistory):
    class Meta:
        app_label = "plmapp"
    plmobject = models.ForeignKey(PLMObject)

class UserHistory(AbstractHistory):
    class Meta:
        app_label = "plmapp"
    plmobject = models.ForeignKey(User)

class GroupHistory(AbstractHistory):
    class Meta:
        app_label = "plmapp"
    plmobject = models.ForeignKey(Group)

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
            default=datetime.datetime.today, auto_now_add=False)
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


