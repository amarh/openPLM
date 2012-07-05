===========================================
Commands
===========================================

Most of the available commands must be run from the main directory where the
file :file:`manage.py` is located.

This script accepts a command followed by mandatory and optional arguments.

Usage: :samp:`./manage.py subcommand [options] [args]`

The following options are always available:

.. option:: -v VERBOSITY, --verbosity=VERBOSITY

    Verbosity level; 0=minimal output, 1=normal output, 2=all output

.. option:: --traceback          
    
    Print traceback on exception. Useful for debugging purpose.
 
.. option:: --settings=SETTINGS 

    The Python path to a settings module, e.g.  "myproject.settings.main". 
    If this isn't provided, the DJANGO_SETTINGS_MODULE environment variable will be used.

.. option:: --pythonpath=PYTHONPATH

    A directory to add to the Python path, e.g.  "/home/djangoprojects/myproject".

.. option:: --version

    show Django's version number
    
.. option:: -h, --help 

    show an help message and exit



Database related commands
============================


The command :program:`./manage.py syncdb` creates 
the database tables for all apps in :const:`~settings.INSTALLED_APPS`
whose tables haven't already been created, except those which use migrations.

.. program:: ./manage.py syncdb

.. option:: --all              

    Makes syncdb work on all apps, even migrated ones. Be careful!
    This option should only be set to initialize if no tables were
    created.


Search index related commands
================================


User related commands
========================
