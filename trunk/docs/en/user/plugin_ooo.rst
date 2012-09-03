=====================================
Plugin for OpenOffice.org/LibreOffice
=====================================


Build and Installation
=======================

Get the sources
----------------

This plugin is available on the svn in the directory :file:`trunk/plugins/openoffice`.

Dependances
-------------

Of course, you need OpenOffice or LibreOffice, this plugin has been test with the version 3.2.
On Linux, you also need to have a valid Python environment (version 2.6) with the library
Poster (available `here <http://atlee.ca/software/poster/#download>`_).

Build
-------------

.. note::
    You can skip this step, download this :download:`file (Windows) <download/openplm-win.oxt>`
    ot this :download:`file (Other) <download/openplm.oxt>`.
    Note that this file may not be up to date.

You just have to made an archive (a zip file) of 3 files, the archive must have
the extension ``.oxt``:

    - if you have a valid poster installation:

        ``zip openplm.oxt Addons.xcu META-INF/manifest.xml openplm.py`` 
    
    - else (this should work on Windows for example):
        
        ``zip openplm.oxt Addons.xcu META-INF/manifest.xml openplm.py pythonpath/*/*`` 


This will create a file called :file:`openplm.oxt` that you can install.

Installation
--------------

There are two ways to install this plugin:

    - the command line
    - the tool include OpenOffice

With the command line
~~~~~~~~~~~~~~~~~~~~~

You just have to install the plugin with the following command:

``unopkg add -f -v openplm.oxt``

.. warning::
    This command installs the plugin for the current user, see the documentation of
    unopkg to make a system installation.

With the extensions manager
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Launch OpenOffice
#. Launch the extension manager: menu :menuselection:`Tools --> Extension Manager...`.
   A dialog should appear:

   .. image:: images/pl_ooo_em.png

#. Then click on the :guilabel:`Add...` button and select the file :file:`openplm.oxt`
#. Now, the plugin is installed, close the dialog and restart openoffice. If the
   plugin is installed, a new menu called :guilabel:`OpenPLM` should be present.

Usage
=====

Configuration
-------------

First, you should specify where the server is located. Open the configuration
dialog (menu :menuselection:`OpenPLM --> Configure`). This dialog should appear:

    .. image:: images/pl_ooo_conf.png

Enter your server's location and click on :guilabel:`Configure`.

Login
-----

Before checking-out a file, you sould login. Open the configuration
dialog (menu :menuselection:`OpenPLM --> Login`). This dialog should appear:

    .. image:: images/pl_ooo_login.png

Enter your username and your password and click on :guilabel:`Login`.

Check-out a file
----------------------

To check-out a file, click on :menuselection:`OpenPLM --> Check-out`.
This dialog should appear:

    .. image:: images/pl_ooo_co1.png

Enter your query and click on the :guilabel:`Search` button, then expand
the item called :guilabel:`Results`. You can browse the documents to see
which files are available by expanding the items:

    .. image:: images/pl_ooo_co2.png

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

    .. image:: images/pl_ooo_ci.png

Check the :guilabel:`Unlock?` button if you want to unlock your file,
this will also close your file in OpenOffice.

Click on the :guilabel:`Check-in` button.

Revise a document
----------------------

To create a new revision of the document link to your file, click on
:menuselection:`OpenPLM --> Revise`. This dialog should appear:

    .. image:: images/pl_ooo_rev.png

Check the :guilabel:`Unlock?` button if you want to unlock your file,
this will also close your file in OpenOffice.

.. note::

    The old revision file is automatically unlock.

Click on the :guilabel:`Revise` button.


Create a new document
-----------------------

You can create a new document from a file which was not checked-out nor
downloaded. Click on :menuselection:`OpenPLM --> Create a document`.
This dialog should appear:

    .. image:: images/pl_ooo_create.png

Fill the form (do not forget the filename with its extension) and
click on :guilabel:`Create` to validate the creation.

Like for a revision or a check-in, check the :guilabel:`Unlock?` button if you
want to unlock your file, this will also close your file in OpenOffice.


Forget a file
-----------------------

All checked-out/downloaded files are opened when you launch OpenOffice,
you can forget a file by clickin on :menuselection:`OpenPLM --> Forget current file`.

Attach a document to a part
----------------------------

You can link the current document to a part by clicking on
:menuselection:`OpenPLM --> Attach to part`. This will display a dialog
to choose the part. Select one and click on the :guilabel:`Attach` button.

