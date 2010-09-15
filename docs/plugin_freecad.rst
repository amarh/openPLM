============================
Plugin for FreeCAD
============================


Installation
=======================

Get the sources
----------------

This plugin is available on the svn in the directory :file:`trunk/plugins/freecad/`.

Dependances
-------------

Of course, you need FreeCAD, this plugin has been test with the versions 0.10 and 0.11.
You also need to have a valid Python environment (version 2.6) with the library
Poster (available `here <http://atlee.ca/software/poster/#download>`_).

Installation
--------------

Just go in the :file:`plugins/freecad` directory and run the command :command:`./install.sh`.

Launch FreeCAD, if the plugin has been successfully installed, a new workbench
named *OpenPLM* is available.

.. warning::
    This will only install the plugin for the current user.

Usage
=====

Configuration
-------------

First, you should specify where the server is located:

    #. Activate the *OpenPLM* workbench.
    #. open the configuration dialog (menu :menuselection:`OpenPLM --> Configure`).
       This dialog should appear:

       .. image:: images/pl_fc_conf.png

    #. Enter your server's location
    #. Click on :guilabel:`Ok`.

Login
-----

Before checking-out a file, you sould login:

    #. Activate the *OpenPLM* workbench.
    #. Open the configuration dialog (menu :menuselection:`OpenPLM --> Login`).
       This dialog should appear:

       .. image:: images/pl_fc_login.png

    #. Enter your username and your password
    #. Click on :guilabel:`Ok`.

Check-out a file
----------------------

To check-out a file, activate the *OpenPLM* workbench. Then, click on :menuselection:`OpenPLM --> Check-out`.
This dialog should appear:

    .. image:: images/pl_fc_co1.png

Enter your query and click on the :guilabel:`Search` button, then expand
the item called :guilabel:`Results`. You can browse the documents to see
which files are available by expanding the items:

    .. image:: images/pl_fc_co2.png

Then select your file and click on the :guilabel:`Check-out` button.
This should open your file, now you can work as usual.

Once you have finished your work, you can revise the document or
check-in it.

Download a file
----------------------

If you just want to visualize a file without modifying it, click on
:menuselection:`OpenPLM --> Download from OpenPLM`. Enter your query,
select your file and click on the :guilabel:`Download` button.

Check-in a file
----------------------

To save your work on the server, click on :menuselection:`OpenPLM --> Check-in`.
This dialog should appear:

    .. image:: images/pl_fc_ci.png

Check the :guilabel:`Unlock?` button if you want to unlock your file,
this will also close your file in FreeCAD.

Click on the :guilabel:`Check-in` button.

Revise a document
----------------------

To create a new revision of the document link to your file, click on
:menuselection:`OpenPLM --> Revise`. This dialog should appear:

    .. image:: images/pl_fc_rev.png

Check the :guilabel:`Unlock?` button if you want to unlock your file,
this will also close your file in FreeCAD.

.. note::

    The old revision file is automatically unlock.

Click on the :guilabel:`Revise` button.


Create a new document
-----------------------

You can create a new document from a file which was not checked-out nor
downloaded. Click on :menuselection:`OpenPLM --> Create a document`.
This dialog should appear:

    .. image:: images/pl_fc_create.png

Fill the form (do not forget the filename with its extension) and
click on :guilabel:`Create` to validate the creation.

Like for a revision or a check-in, check the :guilabel:`Unlock?` button if you
want to unlock your file, this will also close your file in FreeCAD.


Forget a file
-----------------------

All checked-out/downloaded files are opened when you launch FreeCAD,
you can forget a file by clickin on :menuselection:`OpenPLM --> Forget current file`.

Attach a document to a part
----------------------------

You can link the current document to a part by clicking on
:menuselection:`OpenPLM --> Attach to part`. This will display a dialog
to choose the part. Select one and click on the :guilabel:`Attach` button.

