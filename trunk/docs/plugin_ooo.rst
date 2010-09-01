============================
Plugin for OpenOffice.org
============================


Build and Installation
=======================

Get the sources
----------------

This plugin is available on the svn in the directory :file:`trunk/plugins/openoffice`.

Dependances
-------------

Of course, you need OpenOffice, this plugin has been test with the version 3.2.
You also need to have a valid Python environment (version 2.6) with the libraty
Poster (available `here <http://atlee.ca/software/poster/#download>`_).

Build
-------------

You just have to made an archive (a zip file) of 3 files, the archive must have
the extension ``.oxt``:

``zip openplm.oxt Addons.xcu META-INF/manifest.xml openplm.py`` 

This will create a file called :file:`openplm.oxt` that you can install.

Installation
--------------

There are two ways to install this plugin:

    - the command line
    - the tool include OpenOffice

With the command line
~~~~~~~~~~~~~~~~~~~~~

You just have to install the plugin with the following:

``unopkg add -f -v openplm.oxt``

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

Download a file
----------------------

Check-in a file
----------------------

Revise a document
----------------------

Create a new document
-----------------------

Forget a file
-----------------------

Attach a document to a part
----------------------------

