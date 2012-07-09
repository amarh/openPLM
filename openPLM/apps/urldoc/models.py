from django.db import models
from django.contrib import admin

from django.utils.translation import ugettext_noop
from django.utils.translation import ugettext_lazy as _

from openPLM.plmapp.models import Document

def register(cls):
    try:
        admin.site.register(cls)
    except admin.sites.AlreadyRegistered:
        pass
        
        
class URLDoc(Document):
    u"""
    URLDoc : object which represent an url
    """
    location_uri= models.CharField(verbose_name=_("location uri"), max_length=250, blank=True, default = " ")
    
    @property
    def attributes(self):
        return super(URLDoc, self).attributes + ["location_uri"]
        
    @property
    def documentation(self):
        pass
        
        
    @property
    def menu_items(self):
        items = super(URLDoc, self).menu_items
        items = items+[ugettext_noop("content")]
        return items

register(URLDoc)    
