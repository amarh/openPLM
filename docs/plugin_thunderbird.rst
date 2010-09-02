============================
Plugin for Thunderbird
============================


Build and Installation
=======================

Get the sources
----------------

This plugin is available on the svn in the directory :file:`trunk/plugins/thunderbird`.

Dependances
-------------

Of course, you need Thunderbird, this plugin has been test with the versions 3.0 and
3.1.

Build
-------------

.. note::
    You can skip this step, download this :download:`file <download/openplm.xpi>`.
    Note that this file may not be up to date.

Just go in the :file:`plugins/thunderbird` directory and run the command :command:`./build.sh`.
This shoul create a file named :file:`openplm.xpi`. 


Installation
--------------

#. Launch Thunderbird
#. Launch the add-ons manager: menu :menuselection:`Tools --> Add-ons`.
   A dialog should appear:

   .. image:: images/pl_th_em.png
        :scale: 90%

#. Then click on the :guilabel:`Install...` button and select the file :file:`openplm.oxt`.
   A dialog asking confirmation should appear:

   .. image:: images/pl_th_em2.png
        :scale: 90%

#. Click on the :guilabel:`Install Now`.
#. Restart Thunderbird
#. Now, the plugin is installed. If the plugin is installed, a new submenu named :guilabel:`OpenPLM` should be present in the :guilabel:`File` menu.

Usage
=====

Configuration
-------------

First, you should specify where the server is located:

    #. Open the dialog (menu :menuselection:`Tools -- Add-ons`).
    #. Select the OpenPLM add-ons:

        .. image:: images/pl_th_em3.png
            :scale: 90%
    
    #. Click on the :guilabel:`Preferences` button. This dialog should appear:
        
        .. image:: images/pl_th_conf.png

    #. Enter your server's location and close the dialog.    


Login
-----

Before checking-in a file, you sould login. Open the configuration
dialog (menu :menuselection:`File --> OpenPLM --> Login`). This dialog should appear:

    .. image:: images/pl_th_login.png

Enter your username and your password and click on :guilabel:`Ok`.

Check-in a mail
----------------------

You can save a mail on the server:
    
    #. Select one or several mails
    #. Click on :menuselection:`File --> OpenPLM --> Check-in current mail`.
       This dialog should appear:

       .. image:: images/pl_th_ci.png

    #. Fill the search form and click on the :guilabel:`Search` button.
    #. Select your document, and click on :guilabel:`Ok`
    #. Your mail has been had.


Create a new document
-----------------------

You can create a new document from a mail:

    #. Select one or several mails
    #. Click on :menuselection:`File --> OpenPLM --> Create a new document`.
       This dialog should appear:

        .. image:: images/pl_th_create.png

    #. Fill the form
    #. Click on :guilabel:`Ok` to validate the creation.
    #. Your document has been created.

