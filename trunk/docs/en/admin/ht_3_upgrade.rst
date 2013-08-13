.. _admin-upgrade:

=============================================
How to upgrade an installation of OpenPLM
=============================================


.. warning::

    Before upgrading your installation, read the whole document and
    be sure to have reliable backups.

You should also read the following instructions:

.. toctree::
    :glob:
    :titlesonly:

    upgrade/*

Stopping the server
===================

    * ``service apache2 stop``

    * ``service celeryd stop``


Backups
============

Database
--------
 
See your database documentation:

 * PostgreSQL: http://www.postgresql.org/docs/9.2/static/backup.html
 

Code
----

Backups are mostly useless if you do not have the code that was running.

Copy the content of :samp:`{/path/to/openPLM/}` (directory containing the :file:`settings.py` file).
You should also copy your apache configuration and your celery files
(``/etc/init.d/celetyd`` and ``/etc/default/celeryd``).

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

Restoring a backup
-------------------

 * Stop apache and celery
 * Restore all files
 * Restore the database
 * Restore the code
 * Restore search indexes or rebuild them

Updating the code
==================

You should remove old ``.pyc`` files:

    * ``find path/to/openPLM -name '*.pyc' -delete``

Development version (svn)
---------------------------

    #. Backup your files, code, **settings.py**, thumbnails...
    #. Check your own modification: ``svn up`` and ``svn diff``
    #. Run ``svn up``
    #. Restore your own settings (svn should have gracefully updated the
       settings.py file)


Stable version (tarball)
--------------------------

Here, openPLM is installed in ``/var/django``.

    #. Backup your files, code, **settings.py**, thumbnails...
    #. Extract the tarball in a temporary directory.
       For example: ``tar xzf openplm-XYZ.tgz -C . /tmp``
    #. Copy the files:
       ``cp -rp /tmp/openplm/openPLM /var/django``,
       ``/var/django`` is the directory containing your ``openPLM`` directory
    #. Restore your :file:`settings.py` file:
       
        * ``cp /var/django/openPLM/settings.py /var/django/openPLM/settings.py.orig``
        * ``cp backups/settings.py /var/django/openPLM``

    #. Fix the python path in apache ``*.wsgi`` files:
       ``sed -in 's#\(/var/django/\)openPLM/trunk/#\1#' apache/*.wsgi``

New settings
=============

It is possible that a new version comes with new settings. 
Generally, new settings are optional and their default values
do not changes the behavior of a previous installation.
New settings may better fit your needs.
You can easily determinate new settings:

 * development version:

    ``diff /path/to/backup/settings.py /path/to/settings.py``
    (svn should have merged your settings and the original settings)

 * tarball:

     ``diff -u /var/django/openPLM/settings.py /var/django/openPLM/settings.py.orig``


Migrating the database
=========================

One simple command:
    
    * ``./manage.py migrate``


Translations
==================

Not required if you update using the tarball:

    #. ``make``
    #. ``./bin/translate_all.sh compile all``


Search indexes
=================

Not really required but some functionalities may run faster.

    #. ``./manage.py rebuild_index``
    #. ``chown www-data:www-data -R /var/openPLM``


Determining if you should rebuild the index
-----------------------------------------------

Rebuilding search indexes can take several minutes depending
on the number of indexed parts, documents and files.
You can try to rebuild indexes and if it takes too much time
you can safely restore your backed up indexes.

Version 1.2:

    * group attribute is indexed and it is now possible to query
      documents by their group (``group=a_group_name``).
      Previously, a query like ``a_group_name`` matched the
      right documents but ``group=a_group_name`` would returned an
      empty result set.

    * OpenPLM 1.2 tests if a search result is readable by the
      current user. If search indexes are not rebuilt, each search
      will hit the database and take a little more time.

Collecting static files
=========================

.. versionadded:: 2.0

Not required if you update using the tarball:

    * ``./manage.py collectstatic``

File permissions
================

    * ``chown www-data:www-data -R /var/openPLM``
    * ``chown www-data:www-data -R /var/django/openPLM/trunk/openPLM/media/thumbnails``
    * ``chown www-data:www-data -R /var/django/openPLM/trunk/openPLM/media/public/thumbnails``
    * ``chown www-data:www-data -R /var/django/openPLM/trunk/openPLM/media/3D`` if ``document3D`` is installed

Enabling new applications
==========================

A new version of OpenPLM often comes with new optional applications.
You can enable them according to your needs.

Other actions
==============

..
    Put stuff specific to a version here

OpenPLM 1.2
-----------

You can load more optional lifecycles:

    * ``./manage.py loaddata extra_lifecycles``


Starting the server
===================

``service celeryd start``

``service apache2 start``

Now you can test and complain if something does not work ;-)


