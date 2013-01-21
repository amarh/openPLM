.. _ecr-admin:

===============================================
ecr - Engineering Change Requests 
===============================================


This application adds Engineering Change Requests.

settings.py
==============

To enable the *ecr* application, it must be enabled in the settings file: add
``'openPLM.apps.ecr'`` to the list of installed applications
(:const:`INSTALLED_APPS`).


Synchronizing the database
==========================

Run ``./manage.py migrate ecr``.

Run ``./manage.py loaddata lifecycles_ecr.json`` to load lifecycles.


Testing
=========

Create an ECR via the creation page.

You can attach any parts or documents to the ECR.
Moreover, a new tab -- *changes* -- is available on each object page.
This tab lists attached ECR.
