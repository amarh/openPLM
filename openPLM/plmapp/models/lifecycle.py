
#! -*- coding:utf-8 -*-

from django.db import models
from openPLM.plmapp.lifecycle import LifecycleList
from openPLM.plmapp.utils import memoize_noarg



# lifecycle stuff

class State(models.Model):
    u"""
    State : object which represents a state in a lifecycle
    
    .. attribute:: name

        name of the state, must be unique
    """
    
    class Meta:
        app_label = "plmapp"

    name = models.CharField(max_length=50, primary_key=True)

    def __unicode__(self):
        return u'State<%s>' % self.name

class Lifecycle(models.Model):
    u"""
    Lifecycle : object which represents a lifecycle
    
    .. attribute:: name

        name of the lifecycle, must be unique

    .. attribute:: official_state

        *official* :class:`.State` of the lifecycle

    .. note::
        A Lifecycle is iterable and each iteration returns a string of
        the next state.

    .. seealso:: :class:`~plmapp.lifecycle.LifecycleList`
        A class that simplifies the usage of a LifeCycle

    """
    
    class Meta:
        app_label = "plmapp"

    STANDARD, CANCELLED, ECR = (1, 2, 3)
    TYPES = (
        (STANDARD, "standard"),
        (CANCELLED, "cancelled"),
        (ECR, "ECR"),
    )

    name = models.CharField(max_length=50, primary_key=True)
    official_state = models.ForeignKey(State)
    type = models.PositiveSmallIntegerField(default=STANDARD, choices=TYPES)

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
        Converts a Lifecycle to a :class:`.LifecycleList` (a list of strings)
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
        if self._states_list is not None:
            return len(self._states_list)
        return self.lifecyclestates_set.count()

    def __iter__(self):
        return iter(self.to_states_list())

    @classmethod
    def from_lifecyclelist(cls, cycle):
        u"""
        Builds a Lifecycle from *cycle*. The built object is save in the database.
        This function creates states which were not in the database
        
        :param cycle: the cycle used to build the :class:`.Lifecycle`
        :type cycle: :class:`~plmapp.lifecycle.LifecycleList`
        :return: a :class:`.Lifecycle`
        """
        
        lifecycle = cls(name=cycle.name,
            official_state=State.objects.get_or_create(name=cycle.official_state)[0])
        if cycle.official_state == cycle[-1]:
            lifecycle.type = cls.ECR
        lifecycle.save()
        for i, state_name in enumerate(cycle):
            state = State.objects.get_or_create(name=state_name)[0]
            lcs = LifecycleStates(lifecycle=lifecycle, state=state, rank=i)
            lcs.save()
        return lifecycle
                
class LifecycleStates(models.Model):
    u"""
    A LifecycleStates links a :class:`.Lifecycle` and a :class:`.State`.
    
    The link is made with a field *rank* to order the states.
    """
    lifecycle = models.ForeignKey(Lifecycle)
    state = models.ForeignKey(State)
    rank = models.PositiveSmallIntegerField()

    
    class Meta:
        app_label = "plmapp"
        unique_together = (('lifecycle', 'state'),)

    def __unicode__(self):
        return u"LifecycleStates<%s, %s, %d>" % (unicode(self.lifecycle),
                                                 unicode(self.state),
                                                 self.rank)

@memoize_noarg
def get_default_lifecycle():
    u"""
    Returns the default :class:`.Lifecycle` used when instanciate a :class:`.PLMObject`
    """
    return Lifecycle.objects.get(name="draft_official_deprecated")

@memoize_noarg
def get_cancelled_lifecycle():
    u"""
    Returns the "cancelled" Lifecycle.
    """
    return Lifecycle.objects.get(name="cancelled")

@memoize_noarg
def get_cancelled_state():
    u"""
    Returns the "cancelled" State.
    """
    return State.objects.get(name="cancelled")


_default_states_cache = {}
def get_default_state(lifecycle=None):
    u"""
    Returns the default :class:`.State` used when instanciate a :class:`.PLMObject`.
    It's the first state of the default lifecycle.
    """

    if not lifecycle:
        lifecycle = get_default_lifecycle()
    state = _default_states_cache.get(lifecycle.name, None)
    if state is None:
        state = lifecycle.first_state
        _default_states_cache[lifecycle.name] = state
    return state

