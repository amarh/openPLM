from django.db import models
from django.contrib import admin

from django.utils.translation import ugettext_noop

from openPLM.plmapp.models import *

def register(cls):
    try:
        admin.site.register(cls)
    except admin.sites.AlreadyRegistered:
        pass

class Package(Part):
    description = models.TextField(blank=True)
    
    @property
    def attributes(self):
        return super(Package,self).attributes + ["description"]
        

class Software(Part):
    licence = models.CharField(max_length=50, blank=False, null=False)
    description = models.TextField(blank=True)
    linobject_developpement = models.BooleanField(default=False)
    public = models.BooleanField(default=False)
    bugtracker_uri = models.CharField(max_length=250, blank=True)
    
    @property
    def attributes(self):
        attrs = ["licence", "description", "linobject_developpement", "public", "bugtracker_uri"]
        return super(Software, self).attributes + attrs
    
    @property    
    def published_attributes(self):
        return super(Software, self).published_attributes + ["licence","linobject_developpement"]
        

register(Software)
        
class Documentation(Part):
        
    def is_promotable(self):
        return self._is_promotable()

register(Documentation)

class Specification(Document):
    spec_uri = models.CharField(max_length=250, blank=True)
    
    @property
    def attributes(self):
        return super(Specification,self).attributes + ["spec_uri"]

register(Specification)

class URLDoc(Document):
    location_uri= models.CharField(max_length=250, blank=True, default = " ")
    
    @property
    def attributes(self):
        return super(URLDoc, self).attributes + ["location_uri"]
        
    @property
    def documentation(self):
        pass
        
        
    @property
    def menu_items(self):
        items = super(URLDoc, self).menu_items
        items.insert(0,ugettext_noop("content"))
        items.remove(ugettext_noop("files"))
        return items

register(URLDoc)    

class DependencyLink(ParentChildLinkExtension):
    """
    Link between two :class:`Software`: the current_software and its dependency

    :model attributes:
        .. attribute:: required
        
           a boolean that indicate wether the depency is required or not
    """ 
    required = models.BooleanField(default=False)
    version_range = models.CharField(max_length=50)
        
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

