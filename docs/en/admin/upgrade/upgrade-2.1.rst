===========================================
Upgrading from OpenPLM 2.0 to OpenPLM 2.1
===========================================

:Date: 2013-08-26

.. seealso::

     :ref:`admin-upgrade`

New/updated dependencies
==============================

.. note::

    Before upgrading dependencies, you should save a list of
    installed versions. You can get one with the command
    ``pip freeze``.


Template lifecycles
======================

You should add specific lifecycles to create document templates:

    * ``./manage.py loaddata template_lifecycles``

You can also create yours with the admin interface. Simply choose
the *Template* type instead of the *Standard* type when you create
a lifecycle.
