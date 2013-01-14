.. _whatsnew-1.2:

.. Images come later, once we are sure we would not have to update them ;)

=========================
What's new in OpenPLM 1.2
=========================

User changes
===============

Navigate
--------

New style
++++++++++

Screenshots:

.. list-table::

    * - .. figure:: /whatsnew/1.2/navigate_2.png
            :align: center
            
            Document

      - .. figure:: /whatsnew/1.2/navigate_3.png
            :align: center

            Part

Revisions management
+++++++++++++++++++++

Two links to the previous and next revisions are now displayed:
    
.. figure:: /whatsnew/1.2/navigate_1.png

Switch to study mode
+++++++++++++++++++++

Now, we can inspect directly one of the elements displayed in navigate:

.. figure:: /whatsnew/1.2/navigate_4.png

Small User Experience improvements
+++++++++++++++++++++++++++++++++++

    * Zoom factor stays when we switch from one object to another.

    * We can drag graph clicking wherever we want in the graph.


Lifecycle
---------

We can add or remove signers in lifecycles:

.. figure:: /whatsnew/1.2/lifecycle_1.png

BOM
----

Comparison
++++++++++++

We can compare the same BOM at two different dates.

Attached documents
+++++++++++++++++++

We can visualize a complete multi-level BOM including its attached documents:

.. figure:: /whatsnew/1.2/bom_1.png

Files
-------

We can access to all uploaded versions of one file:

.. figure:: /whatsnew/1.2/files_1.png

Badges
------

Change management
------------------


Administrator changes
=======================

New application: badges
-----------------------

A new application, :ref:`badges <badges-admin>` can be installed.
It adds badges ala StackOverflow.


New application: calendrier
-----------------------------

A new application, :ref:`calendrier <calendrier-admin>` can be installed.
It adds a calendar view of the timeline and histories pages and an ICal feed
for each object.


New application: ecr: change management
---------------------------------------

A new application, :ref:`ecr <calendrier-admin>` can be installed.
It adds Engineering Change Request objects.


Optional lifecycles
--------------------

New lifecycles are available, you can load them by running the command
``./manage.py loaddata extra_lifecycles``


Developer changes
==================


Previous versions
=================

.. toctree::
    :maxdepth: 1
    :glob:

    whatsnew/*
