===========================================
Upgrading from OpenPLM 1.2 to OpenPLM 2.0
===========================================

:Date: 2013-08-07

.. seealso::

     :ref:`admin-upgrade`

New/updated dependencies
==============================

.. note::

    Before upgrading dependencies, you should save a list of
    installed versions. You can get one with the command
    ``pip freeze``.

Django 1.5
+++++++++++++++++

OpenPLM 1.2 depends on Django 1.2 or Django 1.3,
OpenPLM 2.0 requires Django 1.5.

    * ``pip install -U 'django==1.5.2'``

Celery 3.0 and Django-Celery 3.0
++++++++++++++++++++++++++++++++++


OpenPLM 1.2 depends on Celery 2.3 or Celery 2.5,
OpenPLM 2.0 is now compatible with Celery 3.0 which is the only version
supported by OpenPLM.

    * ``pip install -U celery django-celery kombu``

You should also install librabbitmq which is recommended by Celery to
connect to RabbitMQ:

    * ``pip install librabbitmq``

South 0.7.6
++++++++++++

South is used to migrate the database. You should always upgrade south
before migrating a database:

    * ``pip install -U 'south==0.7.6'``

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

Python Markdown
++++++++++++++++++
    
You must install Python Markdown (version 2.2.1 or later)
if you want to use Markdown as the syntax of comments and description fields:

    * ``pip install -U Markdown``

Settings
==============

Required
++++++++++++

.. data:: PROJECT_ROOT

    Add the following line at the top of file::

        import sys
        import os.path

        PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))


.. data:: ALLOWED_HOSTS

    It must be set to a list of strings representing the host/domain names that this Django site can serve.

    For example::

        ALLOWED_HOSTS = [
            '.example.com', # Allow domain and subdomains
            '.example.com.', # Also allow FQDN and subdomains
        ]

    See :setting:`django:ALLOWED_HOSTS`


.. data:: COMMENT_APPS

    Must be set to::
        
        COMMENTS_APP = "openPLM.plmapp"

.. data:: USE_TZ

    Must be set to::

        USE_TZ = True

.. data:: BROKER_URL

    Adds the following lines after all ``BROKER_*`` lines::
                
        BROKER_URL = "amqp://%s:%s@%s:%d/%s" % (BROKER_USER,
                BROKER_PASSWORD, BROKER_HOST, BROKER_PORT, BROKER_VHOST)
        del BROKER_USER, BROKER_PASSWORD, BROKER_HOST, BROKER_PORT, BROKER_VHOST

.. data:: INSTALLED_APPS

    The first installed applications must be::

        INSTALLED_APPS = (
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.sites',
            'django.contrib.admin',
            'django.contrib.comments',
            'django.contrib.humanize',
            'django.contrib.messages',
            'django.contrib.staticfiles',
            'djcelery',
            'haystack',
            'south',
            'openPLM.plmapp',
            # your optional applications are set here
        )


.. data:: STATIC_ROOT

    Must be set to::
        
        STATIC_ROOT = os.path.join(PROJECT_ROOT, "static")
        

.. data:: STATIC_URL
    
    Must be set to::
        
        STATIC_URL = "/static/"


.. data:: TEMPLATE_LOADERS

    Must be set to::

        TEMPLATE_LOADERS = (
            "django.template.loaders.filesystem.Loader",
            "django.template.loaders.app_directories.Loader",
        )

    or (cached version)::

        TEMPLATE_LOADERS = (
            ('django.template.loaders.cached.Loader', (
                "django.template.loaders.filesystem.Loader",
                "django.template.loaders.app_directories.Loader",
            )),
        )

.. data:: MIDDLEWARE_CLASSES

    Must be set to::
                
        MIDDLEWARE_CLASSES = (
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
            'openPLM.plmapp.middleware.locale.ProfileLocaleMiddleware',
        )


.. data:: TEMPLATE_CONTEXT_PROCESSORS

    Must be set to::

        TEMPLATE_CONTEXT_PROCESSORS = (
                "django.contrib.auth.context_processors.auth",
                "django.core.context_processors.debug",
                "django.core.context_processors.i18n",
                "django.core.context_processors.media",
                "django.core.context_processors.static",
                "django.core.context_processors.request",
                "django.contrib.messages.context_processors.messages",
        )

.. data:: LOCALE_PATHS
    
    Must be set to::

        LOCALE_PATHS = (
            os.path.join(PROJECT_ROOT, "locale"),
        )

Removed
++++++++++

The settings ``AUTH_PROFILE_MODULE`` and ``ADMIN_MEDIA_PREFIX`` are no longer required
and can be safely removed.


Optional
++++++++++

.. data:: RICHTEXT_FILTER and RICHTEXT_WIDGET_CLASS

    These settings set the wiki syntax used by comments and description fields.

    To enable the Markdown syntaxe, add the following lines::

        RICHTEXT_FILTER = 'openPLM.plmapp.filters.markdown_filter'
        RICHTEXT_WIDGET_CLASS = 'openPLM.plmapp.widgets.MarkdownWidget'

    See :ref:`richtext-admin`.
    
.. data:: REFERENCE_PATTERNS

    This setting describes how new document and part references are generated.
    See :ref:`admin-references`.


Applications
===================

Badges
++++++++

If the badges application is installed, set the ``MIDDLEWARE_CLASSES`` setting to::


    MIDDLEWARE_CLASSES = (
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'openPLM.plmapp.middleware.locale.ProfileLocaleMiddleware',
        'openPLM.apps.badges.middleware.GlobalRequest',
    )

Commands
==============

It is necessary to run the following commands to serve all static files:

    * ``./manage.py collectstatic --noinput``

Apache
================
   
Apache must serve the ``static/`` folder. It must also be able to write in the ``media/`` directory.

    * ``chown -R www-data:www-data media/``

Apache files look like:

.. literalinclude:: ../apache/simple_2.0.conf
    :language: apache

SSL:

.. literalinclude:: ../apache/ssl_2.0.conf
    :language: apache

Ad the following lines if document3D application is installed (befor the ``<Location /media>`` line):

.. code-block:: apache

    <Location /media/3D>
        WSGIAccessScript /var/django/openPLM/trunk/openPLM/apache/access.wsgi
    </Location>


celeryd
========

The init script (:file:`/etc/init.d/celeryd`) has been updated.
It now creates the :file:`/var/log/celery` and :file:`/var/run/celery` directories on startup.

You can copy the new file:

    * ``cp etc/init.d/celeryd /etc/default/celeryd``



