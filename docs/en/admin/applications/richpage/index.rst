.. _richpage-admin:

===============================================
richpage - Page document (wiki page)
===============================================

.. versionadded:: 2.0

This application adds a new type of document, **Page** which
does not contain files but has an editable "content" field.

settings.py
==============

To enable the *richage* application, it must be enabled in the settings file: add
``'openPLM.apps.richpage'`` to the list of installed applications
(:setting:`INSTALLED_APPS`).


You should also enable a :ref:`richtext syntax <richtext-admin>`.


Synchronizing the database
==========================

Run ``./manage.py migrate richpage``.


Testing
=========

Create a Page via the creation page.

Then you can edit its content by clickibng on the :guilabel:`Edit` button.


