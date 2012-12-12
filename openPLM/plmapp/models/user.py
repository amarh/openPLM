
from django.db import models
from django.db.models.signals import post_save
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.encoding import iri_to_uri
from django.utils.translation import ugettext_lazy as _

# user stuff
class UserProfile(models.Model):
    """
    Profile for a :class:`~django.contrib.auth.models.User`
    """
   
    class Meta:
        app_label = "plmapp"
    
    user = models.ForeignKey(User, unique=True)
    #: True if user is an administrator
    is_administrator = models.BooleanField(default=False, blank=True)
    #: True if user is a contributor
    is_contributor = models.BooleanField(default=False, blank=True)
    #: .. versionadded:: 1.1 True if user can publish a plmobject
    can_publish = models.BooleanField(default=False, blank=True)
    #: .. versionadded:: 1.1 True if user has a restricted account
    restricted = models.BooleanField(default=False, blank=True)

    #: language
    language = models.CharField(max_length=5, default="en",
            choices=settings.LANGUAGES)
    
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
        u""" Rank of the user: "administrator", "contributor" or "viewer" """
        if self.is_administrator:
            return _("administrator")
        elif self.is_contributor:
            return _("contributor")
        elif self.restricted:
            return _("restricted account")
        else:
            return _("viewer")

    @property
    def attributes(self):
        u"Attributes to display in `Attributes view`"
        return ["first_name", "last_name", "email", 
                "date_joined", "last_login", "rank"]

    @property
    def menu_items(self):
        "menu items to choose a view"
        if self.restricted:
            return ["attributes", "parts-doc-cad"]
        return ["attributes", "history", "parts-doc-cad", "delegation",
                "groups"]
   

def add_profile(sender, instance, created, **kwargs):
    """ function called when a user is created to add his profile """
    if sender == User and created:
        profile = UserProfile(user=instance)
        profile.save()

if __name__ == "openPLM.plmapp.models.user":
    post_save.connect(add_profile, sender=User)

