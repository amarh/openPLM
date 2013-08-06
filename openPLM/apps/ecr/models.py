from django.utils import timezone

from django.db import models
from django.contrib.auth.models import User
from django.utils.encoding import iri_to_uri
from django.utils.html import conditional_escape as esc
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop
from django.forms.util import ErrorList

from openPLM.plmapp.utils import level_to_sign_str
import openPLM.plmapp.models as pmodels
from openPLM.plmapp.utils import memoize_noarg

_menu_items = pmodels.PLMObject.menu_items

def menu_items(self):
    return _menu_items.fget(self) + [ugettext_noop("changes")]

pmodels.PLMObject.menu_items = property(menu_items)


class ECR(models.Model, pmodels.IObject):
    u"""
    ECR (Engineering Change Request) model.

    :key attributes:
        .. attribute:: reference

            Reference of the :class:`.ECR`, for example ``ECR_0001``

    :other attributes:
        .. attribute:: name

            Name of the ECR, for example ``Game of life``

        .. attribute:: description

            long description of the ECR
        .. attribute:: creator

            :class:`~django.contrib.auth.models.User` who created the :class:`.ECR`
        .. attribute:: creator

            :class:`~django.contrib.auth.models.User` who owns the :class:`.ECR`
        .. attribute:: ctime

            date of creation of the object (default value : current time)
        .. attribute:: mtime

            date of last modification of the object (automatically field at each save)
        .. attribute:: lifecycle

            :class:`.Lifecycle` of the object
        .. attribute:: state

            Current :class:`.State` of the object
        .. attribute:: reference_number

            number found in the reference if it matches ``ECR_\d+``

    """

    # key attributes
    reference = models.CharField(_("reference"), max_length=50, db_index=True, unique=True,
                                 help_text=_(u"Required. 50 characters or fewer. Letters, numbers , except #, ?, / and .. characters"))

    # hidden field to get a valid new reference
    reference_number = models.IntegerField(default=0)

    # other attributes
    name = models.CharField(_("name"), max_length=100, blank=True,
                            help_text=_(u"Name of the ECR"))
    description = models.TextField(_("description"), blank=True)
    description.richtext = True

    creator = models.ForeignKey(User, verbose_name=_("creator"),
                                related_name="%(class)s_creator")
    owner = models.ForeignKey(User, verbose_name=_("owner"),
                              related_name="%(class)s_owner")
    ctime = models.DateTimeField(_("date of creation"), default=timezone.now,
                                 auto_now_add=False)
    mtime = models.DateTimeField(_("date of last modification"), auto_now=True)

    # state and lifecycle
    lifecycle = models.ForeignKey(pmodels.Lifecycle, verbose_name=_("lifecycle"),
                                  related_name="+",)
    state = models.ForeignKey(pmodels.State, verbose_name=_("state"),
                              related_name="+",)

    class Meta:
        # keys in the database
        ordering = ["reference"]

    def __init__(self, *args, **kwargs):
        # little hack:
        # get_creation_fields is a class method but it needs to create
        # an instance, this hack avoids calls to default value functions
        if "__fake__" not in kwargs:
            super(ECR, self).__init__(*args, **kwargs)
        self._promotion_errors = None

    def __unicode__(self):
        return u"ECR<%s>" % self.reference

    @property
    def title(self):
        attrs = (esc(self.reference), esc(self.name))
        return mark_safe(u'''<span class="type">ECR</span> // <span class="reference">%s</span>
 // <span class="name">%s</span>''' % attrs)

    def is_promotable(self):
        """
        Returns True if the object's state is the last state of its lifecycle.
        """
        self._promotion_errors = ErrorList()
        if self.lifecycle.last_state == self.state:
            self._promotion_errors.append(_(u"The object is at its last state."))
            return False
        return True

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
        """
        return False

    @property
    def is_editable(self):
        """
        True if the object is not in a non editable state
        """
        return self.is_draft and not self.approvals.now().exists()

    @property
    @pmodels.cache_lifecycle_stuff
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
    @pmodels.cache_lifecycle_stuff
    def is_cancelled(self):
        """ True if the object is cancelled. """
        return self.lifecycle == pmodels.get_cancelled_lifecycle()

    @property
    @pmodels.cache_lifecycle_stuff
    def is_deprecated(self):
        """ Always returns False since an ECR can not be deprecated"""
        return False

    @property
    @pmodels.cache_lifecycle_stuff
    def is_official(self):
        u"Returns True if object is official."""
        return not self.is_cancelled and self.state == self.lifecycle.official_state

    @property
    @pmodels.cache_lifecycle_stuff
    def is_draft(self):
        u""" Returns True if the object is a draft. """
        return not self.is_cancelled and self.state == self.lifecycle.first_state

    @pmodels.cache_lifecycle_stuff
    def get_current_sign_level(self):
        """
        Returns the current sign level that a user must have to promote this
        object.
        """
        rank = pmodels.LifecycleStates.objects.get(state=self.state,
                            lifecycle=self.lifecycle).rank
        return level_to_sign_str(rank)

    @pmodels.cache_lifecycle_stuff
    def get_previous_sign_level(self):
        """
        Returns the current sign level that a user must have to demote this
        object.
        """
        rank = pmodels.LifecycleStates.objects.get(state=self.state,
                            lifecycle=self.lifecycle).rank
        return level_to_sign_str(rank - 1)

    @property
    def attributes(self):
        u"Attributes to display in `Attributes view`"
        return ["reference", "name", "description", "creator", "owner",
                "ctime", "mtime"]

    @property
    def menu_items(self):
        "Menu items to choose a view"
        return [ugettext_noop("attributes"), ugettext_noop("lifecycle"),
                ugettext_noop("history"), ugettext_noop("part-doc-cads"),
               ]

    @property
    def plmobject_url(self):
        return iri_to_uri(u"/ecr/%s/" % self.reference)

    @classmethod
    def get_creation_fields(cls):
        """
        Returns fields which should be displayed in a creation form.
        """
        return ["name", "reference", "description", "lifecycle"]

    @classmethod
    def get_modification_fields(cls):
        """
        Returns fields which should be displayed in a modification form
        """
        return ["name", "description"]

    def get_current_signer_role(self):
        lcl = self.lifecycle.to_states_list()
        return level_to_sign_str(lcl.index(self.state.name))

    def get_current_signers(self):
        role = self.get_current_signer_role()
        return self.users.now().filter(role=role).values_list("user", flat=True)

    def get_approvers(self):
        if self.is_official or self.is_cancelled:
            return self.approvals.none()
        lcl = self.lifecycle.to_states_list()
        next_state = lcl.next_state(self.state.name)
        approvers = self.approvals.now().filter(current_state=self.state,
                next_state=next_state).values_list("user", flat=True)
        return approvers

    @property
    def is_part(self):
        return False
    @property
    def is_document(self):
        return False
    @property
    def type(self):
        return "ECR"


class ECRHistory(pmodels.AbstractHistory):

    plmobject = models.ForeignKey(ECR)

    def get_redirect_url(self):
        return "/history_item/ecr/%d/" % self.id


class ECRPLMObjectLink(pmodels.Link):
    ecr = models.ForeignKey(ECR, related_name="plmobjects")
    plmobject = models.ForeignKey(pmodels.PLMObject, related_name="ecrs")

    class Meta:
        unique_together = ("ecr", "plmobject", "end_time")

    def __unicode__(self):
        return u"ECRPLMObjectLink<%s, %s>" % (self.ecr, self.plmobject)


class ECRUserLink(pmodels.Link):
    """
    Link between a :class:`~.django.contrib.auth.models.User` and a
    :class:`.ECR`

    :model attributes:
        .. attribute:: ecr

            a :class:`.ECR`
        .. attribute:: user

            a :class:`.User`
        .. attribute:: role

            role of *user* for *ecr* (like `owner` or `notified`)
    """

    ACTION_NAME = "Link : ECR-user"

    ecr = models.ForeignKey(ECR, related_name="users")
    user = models.ForeignKey(User, related_name="ecrs")
    role = models.CharField(max_length=30, choices=zip(pmodels.ROLES, pmodels.ROLES),
            db_index=True)

    class Meta:
        unique_together = ("ecr", "user", "role", "end_time")
        ordering = ["user", "role", "ecr__reference",]

    def __unicode__(self):
        return u"ECRUserLink<%s, %s, %s>" % (self.ecr, self.user, self.role)

class ECRPromotionApproval(pmodels.Link):
    """
    Model to track a promotion approval

    :model attributes:
        .. attribute:: ecr

            approved :class:`.ECR`
        .. attribute:: user

            :class:`.User` who approved the promotion
        .. attribute:: current_state

            current :class:`.State` of :attr:`ecr`
        .. attribute:: next_state

            next :class:`.State` of :attr:`ecr` when if will be promoted

    """
    ecr = models.ForeignKey(ECR, related_name="approvals")
    user = models.ForeignKey(User, related_name="ecr_approvals")
    current_state = models.ForeignKey(pmodels.State, related_name="+")
    next_state = models.ForeignKey(pmodels.State, related_name="+")

    class Meta:
        unique_together = ("ecr", "user", "current_state", "next_state", "end_time")


@memoize_noarg
def get_default_lifecycle():
    u"""
    Returns the default :class:`.Lifecycle` used when instanciate a :class:`.ECR`
    """
    return pmodels.Lifecycle.objects.filter(type=pmodels.Lifecycle.ECR).order_by('name')[0]


