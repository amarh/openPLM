.. _whatsnew-1.2:

.. Images come later, once you are sure you would not have to update them ;)

=========================
What's new in OpenPLM 1.2
=========================

What's new for users
=====================

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

Now, you can inspect directly one of the elements displayed in navigate:

.. figure:: /whatsnew/1.2/navigate_4.png

Small User Experience improvements
+++++++++++++++++++++++++++++++++++

    * Zoom factor stays when switching from one object to another.

    * You can drag graph by clicking wherever you want in the graph.


Upload and create
------------------

You can now upload a file (or more) and create a new document
in a few clicks.


.. raw:: html

    <div>
        <br/>
        <video width="700" height="375" controls="controls">
          <source src="_downloads/upload.webm" type="video/webm" />
          Upload of a file
        </video>
    </div>

:download:`Download the video </whatsnew/1.2/upload.webm>`


Lifecycle
---------

It is now possible to asked several signers to promote or demote
a part or document.
The owner can be one of the first signers and he can easily warn other
users when he think its work is ready.

.. figure:: /whatsnew/1.2/lifecycle_1.png

BOM
----

Comparison
++++++++++++

You can compare the same BOM at two different dates.

Attached documents
+++++++++++++++++++

You can visualize a complete multi-level BOM including all attached documents:

.. figure:: /whatsnew/1.2/bom_1.png


Alternate links
+++++++++++++++++

It is possible to create a set of alternate parts.
Each usage of a part can be replaced by one of its alternate.
It is possible to include alternate parts in all BOM.

OpenPLM prevents incoherent situations (like a part parent
of one of its alternate) when BOM are built.

Files
-------

You can access to all uploaded versions of one file:

.. figure:: /whatsnew/1.2/files_1.png

Badges
------

Change management
------------------

Miscellaneous enhancements
----------------------------

    * When creating a part or a document, the group is set to the
      last selected group

    * It is possible to choose the group of a new revision

    * For each part and document, similar contents are displayed on
      the attributes page
  

What's new for administrators
===============================

Documentation
-------------

    * A new how-to, :ref:`admin-upgrade`, is available. 

New settings
------------

    * :const:`~settings.EMAIL_FAIL_SILENTLY`
    * :const:`~settings.KEEP_ALL_FILES`

Minor file revisions
--------------------

A notable change of this version is the ability of openPLM to keep
old minor revision of all files (all check-ins).
You can configure which files are kept, see :mod:`plmapp.files.deletable`.


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


Previous versions
=================

.. toctree::
    :maxdepth: 1
    :glob:

    whatsnew/*
