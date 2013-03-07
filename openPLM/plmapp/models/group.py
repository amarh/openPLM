import random
from django.utils import timezone

from django.db import models

from django.contrib.auth.models import User, Group
from django.utils.html import conditional_escape as esc
from django.utils.safestring import mark_safe
from django.utils.encoding import iri_to_uri
from django.utils.translation import ugettext_lazy as _

class GroupInfo(Group):
    u"""
    Class that stores additional data on a :class:`Group`.
    """

    class Meta:
        app_label = "plmapp"

    description = models.TextField(blank=True)
    description.richtext = True
    creator = models.ForeignKey(User, related_name="%(class)s_creator")

    owner = models.ForeignKey(User, verbose_name=_("owner"),
                              related_name="%(class)s_owner")
    ctime = models.DateTimeField(_("date of creation"), default=timezone.now,
                                 auto_now_add=False)
    mtime = models.DateTimeField(_("date of last modification"), auto_now=True)

    def __init__(self, *args, **kwargs):
        if "__fake__" not in kwargs:
            super(GroupInfo, self).__init__(*args, **kwargs)

    @property
    def title(self):
        return mark_safe(u"""<span class="type">Group</span> // <span class="name">%s</span>""" % esc(self.name))

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
    def get_creation_fields(cls):
        """
        Returns fields which should be displayed in a creation form.
        """
        return ["name", "description"]

    @classmethod
    def get_modification_fields(cls):
        """
        Returns fields which should be displayed in a modification form
        """
        return ["description"]

    @property
    def is_editable(self):
        return True


class Invitation(models.Model):

    class Meta:
        app_label = "plmapp"

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
    ctime = models.DateTimeField(_("date of creation"), default=timezone.now,
                                 auto_now_add=False)
    validation_time = models.DateTimeField(_("date of validation"), null=True)
    guest_asked = models.BooleanField(_("True if guest created the invitation"))
    token = models.CharField(max_length=155, primary_key=True,
            default=lambda:str(random.getrandbits(512)))
