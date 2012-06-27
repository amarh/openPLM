.. _subversion-admin:

===============================================
subversion -- Subversion Repository Application
===============================================

This application adds a **SubversionRepository** document which links to a svn
repository. 


Dependencies
==============

The *subversion* application adds the following dependency:

    * `pysvn <http://pysvn.tigris.org/>`_

settings.py
==============

To enable the *subversion* application, it must be enabled in the settings file: add
``'openPLM.apps.subversion'`` to the list of installed applications
(:const:`INSTALLED_APPS`).

Synchronize the database
========================

Run ``./manage.py migrate subversion``.

Testing
=========

To test this application, create a new SubversionRepository.
The *logs* page can display the last changesets if openPLM succeeds to retreive
them.

openPLM will *not* ask for a password to connect to a svn repository.


