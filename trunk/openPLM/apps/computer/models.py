############################################################################
# openPLM - open source PLM
# Copyright 2010 Philippe Joulaud, Pierre Cosquer
#
# This file is part of openPLM.
#
#    openPLM is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    openPLM is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with openPLM.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact :
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pcosquer@linobject.com
################################################################################

from django.db import models
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop

from openPLM.plmapp.models import Part, ParentChildLinkExtension, register_PCLE
from openPLM.plmapp.controllers import PartController

def register(cls):
    try:
        admin.site.register(cls)
    except admin.sites.AlreadyRegistered:
        pass

# single part
class SinglePart(Part):

    supplier = models.CharField(verbose_name=_("supplier"),max_length=200)
    tech_details = models.TextField(verbose_name=_("tech details"),blank=True)
    tech_details.richtext = True

    @property
    def attributes(self):
        attrs = list(super(SinglePart, self).attributes)
        attrs.extend([ugettext_noop("supplier"), ugettext_noop("tech_details")])
        return attrs

class SinglePartController(PartController):
    def __init__(self, *args):
        #print "passage dans SinglePartController"
        PartController.__init__(self, *args)

register(SinglePart)

class MotherBoard(SinglePart):
    motherboard_type = models.CharField(verbose_name=_("motherboard type"), max_length=200)

    @property
    def attributes(self):
        attrs = list(super(MotherBoard, self).attributes)
        attrs.extend(["motherboard_type"])
        return attrs

register(MotherBoard)

class ReferenceDesignator(ParentChildLinkExtension):

    reference_designator = models.CharField(verbose_name=_("reference designator"),max_length=200, blank=True)

    def __unicode__(self):
        return u"ReferenceDesignator<%s>" % self.reference_designator

    @classmethod
    def get_visible_fields(cls):
        return ("reference_designator", )

    @classmethod
    def apply_to(cls, parent):
        return isinstance(parent, MotherBoard)

    def clone(self, link, save, **data):
        ref = data.get("reference_designator", self.reference_designator)
        clone = ReferenceDesignator(link=link, reference_designator=ref)
        if save:
            clone.save()
        return clone

register(ReferenceDesignator)
register_PCLE(ReferenceDesignator)


class RAM(SinglePart):
    size_in_mo = models.PositiveIntegerField(verbose_name=_("size in mo"))

    @property
    def attributes(self):
        attrs = list(super(RAM, self).attributes)
        attrs.extend(["size_in_mo"])
        return attrs

register(RAM)


class HardDisk(SinglePart):
    capacity_in_go = models.PositiveIntegerField(verbose_name=_("capacity in go"))

    @property
    def attributes(self):
        attrs = list(super(HardDisk, self).attributes)
        attrs.extend(["capacity_in_go"])
        return attrs

register(HardDisk)


class ElectronicPart(SinglePart):

    pass
register(ElectronicPart)


class MechanicalPart(SinglePart):

    pass

register(MechanicalPart)


class Mouse(SinglePart):
    number_of_buttons = models.PositiveSmallIntegerField(verbose_name=_("number of buttons"), default=lambda: 3)

    @property
    def attributes(self):
        attrs = list(super(Mouse, self).attributes)
        attrs.extend(["number_of_buttons"])
        return attrs

register(Mouse)


class KeyBoard(SinglePart):
    KEYMAPS = (("qw", "Qwerty"),
               ("az", "Azerty"),
              )
    keymap = models.CharField(verbose_name=_("keymap"), max_length=20, choices=KEYMAPS)

    @property
    def attributes(self):
        attrs = list(super(KeyBoard, self).attributes)
        attrs.extend(["keymap"])
        return attrs

register(KeyBoard)


class Screen(SinglePart):
    horizontal_resolution = models.IntegerField(verbose_name=_("horizontal resolution"))
    vertical_resolution = models.IntegerField(verbose_name=_("vertical resolution"))

    @property
    def attributes(self):
        attrs = list(super(Screen, self).attributes)
        attrs.extend(["horizontal_resolution", "vertical_resolution"])
        return attrs

register(Screen)


# assembly

class Assembly(Part):
    manufacturer = models.CharField(verbose_name=_("manufacturer"), max_length=200)

    @property
    def attributes(self):
        attrs = list(super(Assembly, self).attributes)
        attrs.extend(["manufacturer"])
        return attrs

register(Assembly)


class ComputerSet(Assembly):
    customer = models.CharField(verbose_name=_("customer"), max_length=200)

    @property
    def attributes(self):
        attrs = list(super(ComputerSet, self).attributes)
        attrs.extend(["customer"])
        return attrs

register(ComputerSet)


class CentralUnit(Assembly):
    tech_characteristics = models.TextField(verbose_name=_("tech characteristics"), blank=True)
    tech_characteristics.richtext = True

    @property
    def attributes(self):
        attrs = list(super(CentralUnit, self).attributes)
        attrs.extend(["tech_characteristics"])
        return attrs

register(CentralUnit)


class OtherAssembly(Assembly):
    tech_details = models.TextField(verbose_name=_("tech details"), blank=True)
    tech_details.richtext = True

    @property
    def attributes(self):
        attrs = list(super(OtherAssembly, self).attributes)
        attrs.extend(["tech_details"])
        return attrs

register(OtherAssembly)

# bios & os

class BiosOs(Part):

    size_in_mo = models.IntegerField(verbose_name=_("size in mo"))

    @property
    def attributes(self):
        attrs = list(super(BiosOs, self).attributes)
        attrs.extend(["size_in_mo"])
        return attrs

register(BiosOs)


