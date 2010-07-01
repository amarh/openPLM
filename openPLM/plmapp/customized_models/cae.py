import os

from django.db import models
from django.contrib import admin

from openPLM.plmapp.filehandlers import HandlersManager
from openPLM.plmapp.models import Document
from openPLM.plmapp.controllers import DocumentController

def register(cls):
    try:
        admin.site.register(cls)
    except admin.sites.AlreadyRegistered:
        pass

class CAE(Document):

    class Meta:
        app_label = "plmapp"

register(CAE)

class Geometry(CAE):
    
    class Meta:
        app_label = "plmapp"

register(Geometry)

class BoundaryConditions(CAE):

    class Meta:
        app_label = "plmapp"

register(BoundaryConditions)

class Mesh(CAE):

    class Meta:
        app_label = "plmapp"

register(Mesh)

class Results(CAE):

    class Meta:
        app_label = "plmapp"

register(Results)

