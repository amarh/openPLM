===============================================
document3D -- Step and 3D documents
===============================================

This application adds a **Document3D** document which can display
a STEP file in the browser via `WebGL <http://www.khronos.org/webgl/>`_. It also adds the ability to
decompose a STEP file into several parts and documents and 
to recompose an up-to-date STEP file.


Dependencies
==============

This application depends on `pythonOCC <http://www.pythonocc.org/>`_. It has been
tested with the version 0.5.

.. versionchanged:: 1.1

It also depends on `POV-Ray <http://www.povray.org/>`_ to generate thumbnails of
STEP file. It has been tested with the version 3.6.1.


settings.py
==============

To enable the *document3D* application, it must be enabled in the settings file: add
``'openPLM.apps.document3D'`` to the list of installed applications
(:const:`INSTALLED_APPS`).

You must also create a directory in media:

    * ``mkdir media/3D/``
    * ``chown www-data:www-data media/3D``

and edit your apache configuration file to add the following lines:
   
.. code-block:: apache

    # WSGIScriptAlias ...
    <Location /media/3D>
        WSGIAccessScript /var/django/openPLM/trunk/openPLM/apache/access.wsgi
    </Location>
    # alias media/ ...


Collecting static files
==========================

Run ``./manage.py collectstatic``.

Synchronize the database
========================

Run ``./manage.py migate document3D && ./manage.py update_index document3D``.
Then restart celery and apache.


Testing
=========

To test this application, create a new Document3D and add a STEP file (a
sample file :file:`document3D/data_test/test.stp` is available).
After a moment, a 3D view will be available via the 3D tab. Your step
file should appear if your browser supports WebGL.

If it does not work, you should check celery's log (in :file:`/var/log/celery/`)
to see if an error happened. A valid conversion should output a line like this one
``[2012-03-12 14:46:48,089: INFO/MainProcess] Task openPLM.apps.document3D.models.handle_step_file[9f732451-1b43-497c-8b89-f726db861941] succeeded in 27.816108942s: True``.

If the 3D view is ok, you can also try to decompose the STEP file:

    #. Attach the document to a draft part with an empty BOM
    #. Go to the "BOM-CHILD" page of the part
    #. A message explaining that the part can be decomposed should appear,
       click on "Yes"
    #. Fill the form and click on the "create" button.
    #. If it's ok, you part should have a complete BOM. Each child part has
       a Document3D attached and each Document3D should be viewable via its 3D tab.
    #. Now, the original STEP file is bound to the BOM, so if a child STEP file is updated,
       or a BOM link is deleted, the STEP file is updated.


.. note::
    You can check whether your browser supports or not WebGL `here <http://get.webgl.org>`_.


