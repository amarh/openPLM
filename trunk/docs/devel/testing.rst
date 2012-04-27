================================
Testing openPLM
================================

Overview
==========

openPLM uses `Django's testing framework <https://docs.djangoproject.com/en/1.3/topics/testing/>`_.
Most tests are unit tests.


Running tests
================

Dependencies
--------------

Tests depend on lxml (package python-lxml). Moreover the :ref:`subversion-admin` and
:ref:`gdoc-admin` are tested, so theirs dependencies must be installed
(it is not necessary to configure an OAuth account).


Settings
-----------

openPLM ships with a settings file named :file:`settings_tests.py`.
Notable changes compared to a standard settings file are:

    * the database is a sqlite3 database
    * files are saved into a tempory folder
    * the xapian index is saved in an in-memory database
    * celery tasks are synchronously run
    * south is not enabled
    * some testing purpose applications are enabled
    * loaded templates are cached (note that this setting may be enabled
      in production)


Running all tests
-------------------

To run all tests:

    * ``cd /path/to/openPLM``
    * ``./manage.py test --settings=settings_tests``

Note that some subversion tests require an access to openplm.org (they
do something similar to ``svn log``).


Running a specific test
----------------------------

It is possible to only test a specific application:

    * ``./manage.py test plmapp --settings=settings_tests``
    * ``./manage.py test pdfgen --settings=settings_tests``
    
It is also possible to run a specific test case:

    * ``./manage.py test plmapp.GroupControllerTestCase --settings=settings_tests``

It is also possible to run a single test:

    * ``./manage.py test plmapp.GroupControllerTestCase.test_create --settings=settings_tests``



Testing document3D app
------------------------

By default, document3D is not tested since it depends on PythonOCC which is not
packaged on all distributions.
To test document3D, the environment variable :envvar:`openPLM3D` must be set to
``enabled``.
For example, the command ``openPLM3D="enabled" ./manage.py test --settings=settings_tests``
runs all tests, including document3D's tests.


Code coverage
================

openPLM ships with a script named :file:`./bin/run_coverage.sh`. This script runs all
tests with `coverage`_. By default,
this script produces an html report into the :file:`coverage_report` directory.
It is possible to produce an XML output by setting the environment variable
:envvar:`TEST_OUTPUT` to ``xml``. This output produces a file in
:file:`tests_results`  in a format compatible with `Cobertura`_. 

.. _coverage: http://nedbatchelder.com/code/coverage/
.. _Cobertura: http://cobertura.sourceforge.net/


Tasks (celery)
================

The file :file:`settings_tests.py` has special celery settings:

    * An in-memory broker is used
    * All tasks are run **synchronously** so that it is easier to check their
      effects. This implies that some possible concurrency bugs can not be detected.
    * Exceptions are propagated.

