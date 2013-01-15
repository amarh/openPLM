=============================================
How to upgrade an installation of OpenPLM
=============================================

Stopping the server
===================

    * ``service apache2 stop``

    * ``service celeryd stop``


Backups
============

Database

Code

Files

Thumbnails

Search indexes


Updating the code
==================


svn up

/!\ settings.py, your own modifications

or 

copy


Migrating the database
=========================


``./manage.py migrate``


Translations
==================

Not required if tarball

    #. ``make``
    #. ``./bin/translate_all.sh compile all``


Search indexes
=================


Not really required but it improves performance.

    #. ``./manage.py rebuild_index``
    #. ``chown www-data:www-data -R /var/openPLM``

File permissions
================


    * ``chown www-data:www-data -R /var/openPLM``
    * ``chown www-data:www-data -R /var/django/openPLM/trunk/openPLM/media/thumbnails``
    * ``chown www-data:www-data -R /var/django/openPLM/trunk/openPLM/media/public/thumbnails``
    * ``chown www-data:www-data -R /var/django/openPLM/trunk/openPLM/media/3D`` if ``document3D`` is installed

Starting the server
===================

``service celeryd start``

``service apache2 start``

Now you can test and complain if something does not work ;-)



