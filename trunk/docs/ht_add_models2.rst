.. _how-to-app:

===================================================
How to add a model (django application)
===================================================

This document describes how to add a model to openPLM.

.. note::

    You should not use your production environment for development purpose.
    It's recommanded to initiate a development environment:
        
        #. copy openPLM's directory in another place
        #. use the :file:`settings.py.sqlite` as settings file (rename it
           :file:`settings.py`)
        #. run :command:`./manage.py sql all`
        #. run :command:`./manage.py syncdb` (this should ask you if you want to 
           create a superuser, accept it)
        #. edit the superuser profile (model UserProfile in the plmapp section)
           and set him as an administrator and a contributor

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

.. literalinclude:: code/bicycle/models.py
    :linenos:
    :end-before: end of imports

First, we import :mod:`~django.db.models` and :mod:`~django.contrib.admin`.
We need *models* to define our models, and we need *admin* to register our
model and make it available on the admin interface.
 
Next, we import some classes and functions from :mod:`openPLM.plmapp`:

    * :class:`.Part` is the base class for models which describe a part;
    * :class:`.PartController` is the base class for part's controller; 
    * :func:`.get_next_revision` is an utility function.
    
First class
=====================

After the import, you can add a new class. The name of this class, would be the
name displayed in the *type* field in search/creation pages.

In our case, we call it **Bicycle**:

.. literalinclude:: code/bicycle/models.py
    :start-after: class Bicycle
    :end-before: bicycle fields
    :linenos:


Custom fields
======================

Adding fields
+++++++++++++++++++++++++

Now, we can add fields to our models. A field describe which data would be
saved in the database.

.. literalinclude:: code/bicycle/models.py
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

.. literalinclude:: code/bicycle/models.py
    :start-after: bicycle properties
    :end-before: excluded_creation_fields
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

These methods are listed in :class:`.PLMObject`.

Here, we will excluded *details* from a creation form:

.. literalinclude:: code/bicycle/models.py
    :start-after: excluded_creation_fields
    :end-before: end Bicycle 
    :linenos:

This code is similar to :ref:`the attributes property <prop-attr>`.
Nevertheless, :meth:`.PLMObject.excluded_creation_fields` is a
:func:`classmethod` since we do not have a :class:`.PLMObject` when we build a
creation form.

The complete class Bicycle
===============================

.. literalinclude:: code/bicycle/models.py
    :pyobject: Bicycle
    :linenos:

The admin interface
=====================

To make our model available on the admin interface, we just have to add this line:

.. literalinclude:: code/bicycle/models.py
    :start-after: end Bicycle
    :end-before: class BicycleController
    :linenos:

syncdb
======================

Now you can test your model. Run the following commands:

    #. :command:`manage.py sql app_name`
    #. :command:`manage.py syncdb`

The last command should output::

   Installing json fixture 'initial_data' from absolute path.
   Installed 10 object(s) from 1 fixture(s)

Then you can run the server with the :command:`./manage.py runserver localhost:8000`.
Open the url http://localhost:8000/home/ and try to create a bicycle.


Controller
=======================

The model describes only which data should be stored on the database and
which attributes should be displayed/editable. You can change *how* the
objects are manipulated by redefining the :class:`.PLMObjectController`
of your model.

In this tutorial, we will change the behaviour when a bicycle is revised.
Here is the code.

.. literalinclude:: code/bicycle/models.py
    :pyobject: BicycleController
    :linenos:

As you can see, we create a class called *BicycleController* which inherits
from :class:`.PartController`. A *PartController* is a controller which manages
some specifities of the parts like their children. Since *Bicycle* inherits
from :class:`.Part`, our controller inherits from *PartController*.
If you name a controller like :samp:`{model}Controller`, it will be associated
to the model named *model*.

In our case, we just override the method :meth:`.PartController.revise` by
adding a detail if the user forget a revision (for example, *c* instead of
*b*). Of course, you can write what you want and, for example, not take
care of *new_revision*.

.. seealso::

    mod:`controllers` and :ref:`how-to-add-a-controller` for more
    details about controllers.


Views and urls
===============


Tests
======================

Alltogether
===============

The complete app is accessible :download:`here <./code/bicycle.tar.gz>`.

models.py:

.. literalinclude:: code/bicycle/models.py
    :linenos:

