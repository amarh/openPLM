from django.db import models
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext_noop

from openPLM.plmapp.models import Part
from openPLM.plmapp.controllers import PartController

def register(cls):
    try:
        admin.site.register(cls)
    except admin.sites.AlreadyRegistered:
        pass

# single part
class SinglePart(Part):
    
    supplier = models.CharField(max_length=200)
    tech_details = models.TextField(blank=True)

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
    motherboard_type = models.CharField(max_length=200)

    @property
    def attributes(self):
        attrs = list(super(MotherBoard, self).attributes)
        attrs.extend(["motherboard_type"])
        return attrs

register(MotherBoard)


class RAM(SinglePart):
    size_in_mo = models.PositiveIntegerField()
    
    @property
    def attributes(self):
        attrs = list(super(RAM, self).attributes)
        attrs.extend(["size_in_mo"])
        return attrs

register(RAM)


class HardDisk(SinglePart):
    capacity_in_go = models.PositiveIntegerField()
    
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
    number_of_buttons = models.PositiveSmallIntegerField(default=lambda: 3)
    
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
    keymap = models.CharField(max_length=20, choices=KEYMAPS)
    
    @property
    def attributes(self):
        attrs = list(super(KeyBoard, self).attributes)
        attrs.extend(["keymap"])
        return attrs

register(KeyBoard)


class Screen(SinglePart):
    horizontal_resolution = models.IntegerField()
    vertical_resolution = models.IntegerField()
    
    @property
    def attributes(self):
        attrs = list(super(Screen, self).attributes)
        attrs.extend(["horizontal_resolution", "vertical_resolution"])
        return attrs

register(Screen)


# assembly

class Assembly(Part):
    manufacturer = models.CharField(max_length=200)
    
    @property
    def attributes(self):
        attrs = list(super(Assembly, self).attributes)
        attrs.extend(["manufacturer"])
        return attrs

register(Assembly)


class ComputerSet(Assembly):
    customer = models.CharField(max_length=200)
    
    @property
    def attributes(self):
        attrs = list(super(ComputerSet, self).attributes)
        attrs.extend(["customer"])
        return attrs

register(ComputerSet)


class CentralUnit(Assembly):
    tech_characteristics = models.TextField(blank=True)
    
    @property
    def attributes(self):
        attrs = list(super(CentralUnit, self).attributes)
        attrs.extend(["tech_characteristics"])
        return attrs

register(CentralUnit)


class OtherAssembly(Assembly):
    tech_details = models.TextField(blank=True)

    @property
    def attributes(self):
        attrs = list(super(OtherAssembly, self).attributes)
        attrs.extend(["tech_details"])
        return attrs

register(OtherAssembly)

# bios & os

class BiosOs(Part):

    size_in_mo = models.IntegerField()

    @property
    def attributes(self):
        attrs = list(super(BiosOs, self).attributes)
        attrs.extend(["size_in_mo"])
        return attrs

register(BiosOs)


