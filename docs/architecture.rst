========================
Architecture overview
========================

This document describes the architecture of OpenPLM.



Main dependencies
=======================

Django and Python
+++++++++++++++++

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

Models
+++++++

Controllers
+++++++++++

base
----

plmobject
---------

part
----

document
--------

user
----

group
-----

Forms
++++++

Views
+++++

base_views
-----------

main
----

api
---

Tests
++++++


Others
+++++++

Custom applications
===================


