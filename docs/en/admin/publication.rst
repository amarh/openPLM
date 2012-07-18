.. _publication_admin:

.. versionadded:: 1.1

===============
Publication
===============


How to grant "publisher" permission
====================================

To allow an user to publish an object, edit its profile (via the admin interface)
and check the :attr:`can_publish` field.

How to disable anonymous publication
========================================

There is no setting for the moment, but you can:

    1. Remove "publisher" permission of all users

    2. Unpublish all objects (see below)

You can also edit the code and send a patch ;-)

How to quickly unpublish all objects
========================================

In a python shell (``./manage.py shell``), execute the following lines::

    >>> from openPLM.plmapp.models import PLMObject
    >>> PLMObject.objects.update(published=False)

(no histories are recorded).



