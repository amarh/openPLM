========================
Architecture overview
========================

This document describes the architecture of openPLM.



Main dependencies
=======================

Django and Python
+++++++++++++++++

OpenPLM is based on `Django <https://www.djangoproject.com/>`_ : a `Python <http://www.python.org/>`_ web framework.
Django follows the `model-view-controller design`.


Celery
+++++++

`Celery <http://celeryproject.org/>`_ is an asynchronous task queue/job queue 
based on distributed message passing. In openPLM, we use Celery (version 2.3) to:

    * send mails
    * update search indexes
    * run cron jobs

.. seealso::
    The documentation of Celery: http://celery.readthedocs.org/en/latest/ .
    
    `RabbitMQ <http://www.rabbitmq.com/>`_, an efficient
    message broker recommended by Celery.

South
+++++

`South <http://south.aeracode.org/>`_ is an intelligent schema and data
migrations for Django projects. All applications of openPLM are managed by
South to ensure easy updates.


Haystack and Xapian
++++++++++++++++++++

`Haystack <http://haystacksearch.org/>`_ is a Django application that provides
modular search for Django.
Haystack makes it possible to plug openPLM with an efficient search engine.
`Xapian <http://xapian.org>`_ is a search engine and `xapian-haystack <https://github.com/notanumber/xapian-haystack>`_ is a backend for use with Haystack and the Xapian.

.. seealso::
    The documentation of Haystack: http://docs.haystacksearch.org/dev/index.html .


Graphviz and PyGraphviz
++++++++++++++++++++++++

`graphviz <http://www.graphviz.org>`_ is a tool to generate graphs. It has a lot
of features to custom the rendering. 
`PyGraphviz <http://networkx.lanl.gov/trac/wiki/PyGraphviz>`_ is a Python binding
for Graphviz. openPLM uses PyGraphviz to generate the graphs of the *Navigate*
page.

Directories
==============

.. code-block:: none

   +-openPLM/
    | apache/                    apache/wsgi files
    | apps/                      optional applications
    | bin/                       misc executable scripts 
    | datatests/                 test data
    | django_xml_test_runner/    an incorporated dependency required to run test
    | etc/                       files that should be copied to /etc (celeryes configuration files)
    | help/                      help messages in reStructuredText format
    | locale/                    translation data
    +-media/                     all media files (served by apache)
    |  css/                     
    |  img/
    |  js/
    +-plmapp/                    core application (most of the code!)
    |  controllers/
    |  decomposers/
    |  customized_models/
    |  filehandlers/
    |  fixtures/
    |  management/
    |  middleware/
    |  templatetags/
    |  thumbnailers/
    |  tests/
    |  views/
    +-templates/                 core templates
    |  blocks/
    |  documents/
    |  groups/
    |  import/
    |  mails/
    |  navigate/
    |  parts/
    |  search/
    |  snippets/
    |  users/

plmapp
======

plmapp is the main application of openPLM. It defines main models, views and
controllers and is the core of openPLM.

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
work to views. But openPLM has several kinds of views (html, api), so to
keep the views simple and stupid, openPLM has controllers.
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

The following figure shows which models a controller manages.
As you can see, *PartController* manages the *Coffee* model since *CoffeeController* does not exist.

.. figure:: uml_models_controllers.*
    :width: 100%

Forms
++++++

openPLM has many forms. Some forms are generated dynamically from a model
(similar to a Django ModelForm). Obviously, views use forms but controllers
also use form. For example, :meth:`.Controller.update_from_form` and
:meth:`.PLMObjectController.create_from_form` take a form as their argument.

Resources:

    * forms module: :mod:`plmapp.forms`

Views
+++++

openPLM splits its views module:

    * all common functions are in the :mod:`~plmapp.base_views` module
    * classical HTML views are in the :mod:`~plmapp.views.main` module
    * ajax views are in the :mod:`~plmapp.views.ajax` module
    * views that handle the HTTP/Json api are in the :mod:`~plmapp.views.api` module

Resources:

    * :mod:`the HTTP api <http_api>`.

Tests
++++++

See :doc:`testing`.

Others
+++++++

A complete list of documented modules is available :doc:`here <modules>`.


Custom applications
===================

See :ref:`applications` and :ref:`how-to-app`.


