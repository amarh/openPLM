===========================================
Upgrading from OpenPLM 1.2 to OpenPLM 1.3
===========================================


New/updated dependencies
==============================

Django 1.5
+++++++++++++++++

``pip install -U 'django==1.5'``

Celery 3.0 and Django-Celery 3.0
++++++++++++++++++++++++++++++++++

``pip install -U celery django-celery kombu``

``librabbitmq``

South 0.7.6
++++++++++++

``pip install -U south``

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

``pip install -U 'django-haystack==1.2.7'``


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

