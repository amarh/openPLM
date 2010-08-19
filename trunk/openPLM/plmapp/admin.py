"""
This small module register all plmapp models for the admin interface
"""

from django.db import models
from django.contrib import admin

import plmapp.models as m

# register all the models from plmapp
# we browse all attributes from plmapp.models
# if an attribute derives from models.Models and the model is not abstract,
# we register it
for attr in dir(m):
    try:
        obj = getattr(m, attr)
        if issubclass(obj, models.Model) and not obj._meta.abstract:
            admin.site.register(obj)
    except (TypeError, admin.sites.AlreadyRegistered), e:
        continue
