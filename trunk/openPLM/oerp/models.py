from django.db import models
from django.contrib import admin

from openPLM.plmapp.models import Part, ParentChildLink


_menu_items = Part.menu_items

def menu_items(self):
    return _menu_items.fget(self) + ["ERP"]

Part.menu_items = property(menu_items)

class OERPProduct(models.Model):

    part = models.ForeignKey(Part, unique=True)
    product = models.IntegerField()

    def __unicode__(self):
        return u"OERPProduct<%s, %s>" % (self.part, self.product)

admin.site.register(OERPProduct)

class OERPBOM(models.Model):

    link = models.ForeignKey(ParentChildLink, unique=True)
    bom = models.IntegerField()

    def __unicode__(self):
        return u"OERPBOM<%s, %s>" % (self.link, self.bom)

admin.site.register(OERPBOM)

class OERPRootBOM(models.Model):

    part = models.ForeignKey(Part, unique=True)
    bom = models.IntegerField()

    def __unicode__(self):
        return u"OERPRootBOM<%s, %s>" % (self.part, self.bom)

admin.site.register(OERPRootBOM)

