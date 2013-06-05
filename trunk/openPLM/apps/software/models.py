from django.db import models
from django.contrib import admin

from django.utils.translation import ugettext_lazy as _

from openPLM.plmapp.models import Part, ParentChildLinkExtension, register_PCLE

def register(cls):
    try:
        admin.site.register(cls)
    except admin.sites.AlreadyRegistered:
        pass


class Package(Part):
    u"""
    Package : represent a package of softwares
    """
    pass


class Software(Part):
    u"""
    Software : object which represents a software

    .. attribute:: licence

        licence of the software
    .. attribute:: linobject_developpement

        a boolean that indicates wether the software is developped by
        linobject or not
    .. attribute:: public

        a boolean that indicates if the software is public
    .. attribute:: bugtracker_uri

        Url for the issue tracker of the software
    """
    licence = models.CharField(verbose_name=_("licence"), max_length=50, blank=False, null=False)
    linobject_developpement = models.BooleanField(verbose_name=_("developed by LinObject"), default=False)
    public = models.BooleanField(verbose_name=_("public"), default=False)
    bugtracker_uri = models.CharField(verbose_name=_("bugtracker uri"), max_length=250, blank=True)

    @property
    def attributes(self):
        attrs = ["licence", "linobject_developpement", "public", "bugtracker_uri"]
        return super(Software, self).attributes + attrs

    @property
    def published_attributes(self):
        return super(Software, self).published_attributes + ["licence","linobject_developpement"]


register(Software)

class DependencyLink(ParentChildLinkExtension):
    """
    Link between two :class:`Software`: the current_software and its dependency

    :model attributes:
        .. attribute:: required

           a boolean that indicate wether the depency is required or not
    """
    required = models.BooleanField(verbose_name=_("required"), default=False)
    version_range = models.CharField(verbose_name=_("version range"), max_length=50,blank=True)

    def __unicode__(self):
        return u"DependencyLink<%d,%s>" % (self.required, self.version_range)

    @classmethod
    def get_visible_fields(cls):
        return ("required","version_range", )

    @classmethod
    def apply_to(cls, parent):
        return isinstance(parent, Software)


    def clone(self, link, save, **data):
        req = data.get("required", self.required)
        clone = DependencyLink(link=link, required=req)
        if save:
            clone.save()
        return clone

register(DependencyLink)
register_PCLE(DependencyLink)

