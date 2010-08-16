from django.db import models
from django.contrib import admin

import plmapp.models as m

# register all the models from plmapp
for attr in dir(m):
    try:
        obj = getattr(m, attr)
        if issubclass(obj, models.Model) and not obj._meta.abstract:
            admin.site.register(obj)
    except (TypeError, admin.sites.AlreadyRegistered), e:
        continue
