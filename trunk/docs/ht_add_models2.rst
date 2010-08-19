===================================================
How to add a model (django application)
===================================================

This document describes how to add a model to openPLM.

Requirements
=============

* Python
* Django models

Create a new application
=========================

The first step is simple: just run the command :command:`./manage.py startapp app_name`
in the :file:`openPLM` directory (replace *app_name* by the name of your new application).
In this how-to, we will call it *bicycle*. The name of the application
must be a `valid Python module name <http://docs.python.org/reference/lexical_analysis.html#identifiers>`_.

Then you must registered your application: edit the variable :const:`INSTALLED_APPS`
in the :file:`openPLM/settings.py` and add your application
(:samp:`'openPLM.{app_name}'`).

For example::

    INSTALLED_APPS = (
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'django.contrib.admin',
        'openPLM.plmapp',
        # you can add your application after this line
        'openPLM.bicycle',
    )

.. note::
    The application must be added after ``'openPLM.plmapp'``.

Imports
====================

Now you can edit the file :file:`openPLM/{app_name}/models.py`, and add some useful imports

.. literalinclude:: code/bicycle.py
    :linenos:
    :end-before: end of imports

.. todo::
    explain import
 

First class
=====================

After the import, you can add a new class. The name of this class, would be the
name displayed in the *type* field in search/creation pages.

In our case, we call it **Bicycle**:

.. literalinclude:: code/bicycle.py
    :start-after: class Bicycle
    :end-before: bicycle fields
    :linenos:


Custom fields
======================

Adding fields
+++++++++++++++++++++++++

Now, we can add fields to our models. A field describe which data would be
saved in the database.

.. literalinclude:: code/bicycle.py
    :start-after: class Bicycle
    :end-before: bicycle properties 
    :linenos:

We add 3 fields:

    nb_wheels
        as it says, the number of wheels

        This field is a :class:`~django.db.models.PositiveIntegerField`.
        As first argument, we give a more comprehensive name that would be
        displayed in the attributes page.

        We also set a default value for this field with ``default=lambda: 2``.
        The *default* argument does not take a value but a function which does
        takes no argument and return a value. Here, we use a `lambda expression
        <http://docs.python.org/tutorial/controlflow.html#lambda-forms>`_
        which always returns *2*.

    color
        the color of the bicycle

        This field is a :class:`~django.db.models.CharField`. With a CharField,
        you must define the *max_length* argument. This is the maximal number of
        characters that can be stored in the database for this field.

        We also set *blank* to True, this means that this field can be empty
        in a form.

    details
        a field for quite long details

        This field is a :class:`~django.db.models.TextField`. This is a field
        that is displayed with a textarea in forms.

.. seealso::

    The Django `model field reference
    <http://docs.djangoproject.com/en/1.2/ref/models/fields/#ref-models-fields>`_ 
    for all types of field that can be used and their arguments
  

Selecting which fields should be displayed
+++++++++++++++++++++++++++++++++++++++++++++

By default, the fields are not displayed. To select which fields should be
displayed, you can override the method
:attr:`~openPLM.plmapp.models.PLMObject.attributes` like in the example above:

.. _prop-attr:

.. literalinclude:: code/bicycle.py
    :start-after: bicycle properties
    :end-before: get_excluded_creation_fields
    :linenos:

:attr:`attributes` is a read-only :func:`property`. This property is a list
of attributes, so all elements must be a valid field name. For example, 
``"spam"`` is not valid since *spam* is not a field of :class:`Bicycle`.
The property should return attributes from the parent class (:class:`Part` in
our case). That's why we call :func:`super`. In our case, we extends Part 
attributes with *nb_wheels*, *color* and *details*

Other methods that can be overridden
+++++++++++++++++++++++++++++++++++++++

There are other methods that can be overridden to select attributes displayed
in creation/modification forms.

These methods are listed in :class:`~openPLM.plmapp.models.PLMObject`.

Here, we will excluded *details* from a creation form:

.. literalinclude:: code/bicycle.py
    :start-after: get_excluded_creation_fields
    :end-before: end Bicycle 
    :linenos:

This code is similar to :ref:`the attributes property <prop-attr>`. Nevertheless,
:meth:`~openPLM.plmapp.models.PLMObject.get_excluded_creation_fields` is a
:func:`classmethod` since we do not have a :class:`PLMObject` when we build a
creation form.

The complete class Bicycle
===============================

.. literalinclude:: code/bicycle.py
    :pyobject: Bicycle
    :linenos:


syncdb
======================

:command:`./manage.py sql app_name`
:command:`./manage.py syncdb`

Controller
=======================

See :mod:`~plmapp.controllers` and :ref:`how-to-add-a-controller` for details
about controllers.

.. literalinclude:: code/bicycle.py
    :pyobject: BicycleController
    :linenos:


Tests
======================

Alltogether
===============

:download:`Plain text <./code/bicycle.py>`

.. literalinclude:: code/bicycle.py
    :linenos:

