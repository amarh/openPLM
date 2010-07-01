===================================================
How to add a model
===================================================

This document describes how to add a model to openPLM.

Requirements
=============

* Python
* Django models

Add a file
=====================

The first step is simple: just add a :file:`.py` file in ``openPLM/plmapp/customized_models``
directory. In this how-to, we will call it :file:`bicycle.py`. The name of the file
must be a `valid Python module name <http://docs.python.org/reference/lexical_analysis.html#identifiers>`_.

Imports
====================

Now you can edit your file, and add some useful imports::

   import os

   from django.db import models
   from django.contrib import admin

   from openPLM.plmapp.models import Part
   from openPLM.plmapp.controllers import PartController
   from openPLM.plmapp.utils import get_next_revision

.. todo::
    explain import
 

First class
=====================

class::

    class Bicycle(Part):

        class Meta:
            app_label = "plmapp"


Custom fields
======================

Adding fields
+++++++++++++++++++++++++

class::
    
    class Bicycle(Part):

        class Meta:
            app_label = "plmapp"
    
        nb_wheels = models.PositiveIntegerField("Number of wheels", default=lambda: 2)
        color = models.CharField(max_length=25, blank=False)
        details = model.TextField()
    
Selecting which fields should be displayed
+++++++++++++++++++++++++++++++++++++++++++++

::
    
    @property
    def attributes(self):
        attrs = list(super(Bicycle, self).attributes)
        attrs.extend(["nb_wheels", "color", "details"])
        return attrs

::

    @classmethod
    def get_excluded_creation_fields(cls):
        return super(Bicycle, self).get_excluded_creation_fields() + ["details"]


syncdb
======================

Controller
=======================

Tests
======================
