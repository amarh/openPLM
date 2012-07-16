.. _webdav-admin:

===============================================
webdav -- WebDAV support
===============================================

.. warning::

    This application is still in early development stage.

This application adds a WebDAV access to the documents
and files stored by openPLM.

Currently, openPLM exports all documents and
follows this tree structure: :samp:`/{type}/{reference}/{revision}/{files*}`.

An user can get one or more files, add file to document
and delete files.

OpenPLM checks that all actions are legal: for example, it prevents
an user from deleting a file of an official document.

Lock, unlock, collections creation and properties edition
are not implemented.

settings.py
==============

To enable the *webdav* application, it must be enabled in the settings file: add
``'openPLM.apps.webdav'`` to the list of installed applications
(:const:`INSTALLED_APPS`).

Apache
=========

Make sure that

.. code-block:: apache

    WSGIPassAuthorization On 

is set on your apache configuration file.

Testing
=========

To test this application, access to :samp:`http://{server}/dav/` with
a WebDAV client and browse your documents.

