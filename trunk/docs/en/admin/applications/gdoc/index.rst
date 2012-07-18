.. _gdoc-admin:

====================================
gdoc -- Google Document Application
====================================

This application adds a **GoogleDocument** document which links to a document
stored in `Google Document <https://docs.google.com/#home>`_. 


Dependencies
==============

The *gdoc* application adds the following dependencies:

    * `gdata <http://code.google.com/intl/fr-FR/apis/gdata/>`_
    * `google-api-python-client <http://code.google.com/p/google-api-python-client/>`_

They are installable through *pip* or *easy_install*:

    * ``pip install gdata google-api-python-client``


OAuth 2
=======

*gdoc* uses OAuth 2 to authenticate an user so that openPLM does not have
to store user passwords.

You must register your application to Google:

    1. Go on https://code.google.com/apis/console/ , if you have never created 
       register an application, this should show you this page:

       .. image:: images/gapi_1.png

    #. Click on the *Create project* button.

       .. image:: images/gapi_2.png

    #. Click on the API access link.

       .. image:: images/gapi_3.png

    #. Click on *Create an OAuth 2.0 client ID...* button, this will pop up
       a form. On the second page, enter your site domain:

       .. image:: images/gapi_4.png

    #. Enter your application domain and validate the form. Your credentials
       are the client ID and client secret fields.

       .. image:: images/gapi_5.png


settings.py
==============

To enable the *gdoc* application, it must be enabled in the settings file: add
``'openPLM.apps.gdoc'`` to the list of installed applications
(:const:`INSTALLED_APPS`).

At the end of the :file:`settings.py` file, adds two variables::
    
    GOOGLE_CONSUMER_KEY = u'client id from Google API access page'
    GOOGLE_CONSUMER_SECRET = u'client secret from Google API access page'

Synchronize the database
========================

Run ``./manage.py migrate gdoc``.

Testing
=========

To test this application, create a new GoogleDocument. You will be redirected
to a page asking you to allow openPLM to access your documents. Accept and
you will be able to select a document from your Google documents.


