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
--------
 
http://www.postgresql.org/docs/9.2/static/backup.html

Code
----

Backups are mostly useless if you do not have the code that was running.

Copy the content of :samp:`{/path/to/openPLM/}` (directory containing the :file:`settings.py` file).

Files
-----

Copy ``/var/openPLM/docs``.


Thumbnails and 3D files
--------------------------

Copy :samp:`{/path/to/openPLM}/media/thumbnails` and :samp:`{/path/to/openPLM}/media/public`.

If `document3D` application is installed, copy :samp:`{/path/to/openPLM}/media/3D`.


Search indexes
----------------

You can also copy ``/var/openPLM/xapian_index``, it is easy to rebuild the index
but it can take a few minutes.


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



