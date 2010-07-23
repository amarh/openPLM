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
    pass

register(CAE)

class Geometry(CAE):
    pass    

register(Geometry)

class BoundaryConditions(CAE):
    pass

register(BoundaryConditions)

class Mesh(CAE):
    pass

register(Mesh)

class Results(CAE):
    pass

register(Results)

