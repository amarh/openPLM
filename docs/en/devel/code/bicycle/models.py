from django.db import models
from django.contrib import admin

from openPLM.plmapp.models import Part
from openPLM.plmapp.controllers import PartController
from openPLM.plmapp.utils import get_next_revision
# end of imports

# class Bicycle
class Bicycle(Part):

    # bicycle fields
    nb_wheels = models.PositiveIntegerField("Number of wheels", default=lambda: 2)
    color = models.CharField(max_length=25, blank=False)
    details = models.TextField(blank=False)
    
    # bicycle properties
    @property
    def attributes(self):
        attrs = list(super(Bicycle, self).attributes)
        attrs.extend(["nb_wheels", "color", "details"])
        return attrs

    # excluded_creation_fields
    @classmethod
    def excluded_creation_fields(cls):
        return super(Bicycle, cls).excluded_creation_fields() + ["details"]

# end Bicycle

admin.site.register(Bicycle)

# class BicycleController
class BicycleController(PartController):

    def revise(self, new_revision):
        if new_revision == get_next_revision(get_next_revision(self.revision)):
            self.details += """
            ----------------
            hello easter egg
            ----------------
            """
            self.save()
        return super(BicycleController, self).revise(new_revision)

# end BicycleController

