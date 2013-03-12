===========================================
Upgrading from OpenPLM 1.2 to OpenPLM 1.3
===========================================

:Date: 2013-03-12

New/updated dependencies
==============================

.. note::

    Before upgrading dependencies, you should save a list of
    installed versions. You can get one with the command
    ``pip freeze``.

Django 1.5
+++++++++++++++++

OpenPLM 1.2 depends on Django 1.2 or Django 1.3,
OpenPLM 1.3 requires Django 1.5.

    * ``pip install -U 'django==1.5'``

Celery 3.0 and Django-Celery 3.0
++++++++++++++++++++++++++++++++++


OpenPLM 1.2 depends on Celery 2.3 or Celery 2.5,
OpenPLM 1.3 is now compatible with Celery 3.0 which is the only version
supported by OpenPLM.

    * ``pip install -U celery django-celery kombu``

You should also install librabbitmq which is recommended by Celery to
connect to RabbitMQ:

    * ``pip install librabbitmq``

South 0.7.6
++++++++++++

South is used to migrate the database. You should always upgrade south
before migrating a database:

    * ``pip install -U south``

psycopg2
++++++++++++++

You may need to upgrade to a newer version of psycopg2 (binding to postgres)
if the following command fails:

    * ``python -c 'from psycopg2.extensions import ISQLQuote'``

When it fails, it outputs something like::

    Traceback (most recent call last):
      File "<string>", line 1, in <module>
    ImportError: No module named psycopg2.extensions

To install a newer version:

    * ``apt-get install libpq-dev``
    * ``pip install -U psycopg2``

Haystack
++++++++++++

The required version of Haystack is still 1.2.7:

    * ``pip install -U 'django-haystack==1.2.7'``


Settings
==============

Required
++++++++++++

ALLOWED_HOSTS

COMMENT_APPS

USE_TZ

AUTH_PROFILE_MODULE

BROKER_URL

INSTALLED_APPS

STATIC_ROOT

STATIC_URL

ADMIN_MEDIA_PREFIX

TEMPLATE_LOADERS

MIDDLEWARE_CLASSES


TEMPLATE_CONTEXT_PROCESSORS


LOCALE_PATHS

Optional
++++++++++

RICHTEXT_FILTER

REFERENCES

Applications
===================

Badges: new required middleware

Commands
==============

Collect static

Apache
================

static files

