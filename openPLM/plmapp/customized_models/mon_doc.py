from django.db import models
from django.contrib import admin

try:
    from openPLM.plmapp.models import Document
except (ImportError, AttributeError):
    from plmapp.models import Document

class MyDocument(Document):

    class Meta:
        app_label = "plmapp"
    my_attr = models.BooleanField()

admin.site.register(MyDocument)
