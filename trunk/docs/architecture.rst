========================
Architecture overview
========================

This document describes the architecture of OpenPLM.



Main dependencies
=======================

Django and Python
+++++++++++++++++

TODO

Celery
+++++++

`Celery <http://celeryproject.org/>`_ is an asynchronous task queue/job queue 
based on distributed message passing. In OpenPLM, we use Celery (version 2.3) to:

    * send mails
    * update search indexes
    * run cron jobs

.. seealso::
    The documentation of Celery: http://celery.readthedocs.org/en/latest/ .
    
    `RabbitMQ <http://www.rabbitmq.com/http://www.rabbitmq.com/>`_, an efficient
    message broker recommended by Celery.

South
+++++

`South <http://south.aeracode.org/>`_ is an intelligent schema and data
migrations for Django projects. All applications of OpenPLM are managed by
South to ensure easy updates.


Haystack and Xapian
++++++++++++++++++++

`Haystack <http://haystacksearch.org/>`_ is a Django application that provides
modular search for Django.
Haystack makes it possible to plug OpenPLM with an efficient search engine.
`Xapian <http://xapian.org>`_ is a search engine and `xapian-haystack <https://github.com/notanumber/xapian-haystack>`_ is a backend for use with Haystack and the Xapian.

.. seealso::
    The documentation of Haystack: http://docs.haystacksearch.org/dev/index.html .


Graphviz and PyGraphviz
++++++++++++++++++++++++

`graphviz <http://www.graphviz.org>`_ is a tool to generate graphs. It has a lot
of features to custom the rendering. 
`PyGraphviz <http://networkx.lanl.gov/trac/wiki/PyGraphviz>`_ is a Python binding
for Graphviz. OpenPLM uses PyGraphviz to generate the graphs of the *Navigate*
page.

plmapp
======

plmapp is the main application of OpenPLM. It defines main models, views and
controllers and is the core of OpenPLM.

Models
+++++++

    A model is the single, definitive source of data about your data. It
    contains the essential fields and behaviors of the data you’re storing.
    
    -- `Django's documentation <https://docs.djangoproject.com/en/1.3/topics/db/models/#module-django.db.models>`_

Resources:

    * Module: :mod:`~openPLM.plmapp.models`
    * :ref:`Related recipes <cookbook-models>`

Controllers
+++++++++++

In Django, applications do not have dedicate controllers and let this kind of
work to views. But OpenPLM has several kinds of views (html, api), so to
keep the views simple and stupid, OpenPLM has controllers.
Controllers manage user's rights (they ensures the user can do the asked action)
and check inputs. Controllers also keep trace of what have been done
(histories) and send mails to affected users. 

Resources:
    
    * :mod:`~plmapp.controllers`
    * base: :mod:`~plmapp.controllers.base`
    * plmobject: :mod:`~plmapp.controllers.plmobject`
    * part: :mod:`~plmapp.controllers.part`
    * document: :mod:`~plmapp.controllers.document`
    * user: :mod:`~plmapp.controllers.user`
    * group: :mod:`~plmapp.controllers.group`


Forms
++++++

OpenPLM has many forms. Some forms are generated dynamically from a model
(similar to a Django ModelForm). Obviously, views use forms but controllers
also use form. For example, :meth:`.Controller.update_from_form` and
:meth:`.PLMObjectController.create_from_form` take a form as their argument.

Resources:

    * forms module: :mod:`plmapp.forms`

Views
+++++

OpenPLM splits its views module:

    * all common functions are in the :mod:`~plmapp.base_views` module
    * classical HTML views are in the :mod:`~plmapp.views.main` module
    * ajax views are in the :mod:`~plmapp.views.ajax` module
    * views that handle the HTTP/Json api are ine the :mod:`~plmapp.views.api` module

Resources:

    * :mod:`the HTTP api <http_api>`.

Tests
++++++


Others
+++++++

Custom applications
===================


