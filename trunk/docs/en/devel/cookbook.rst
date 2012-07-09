.. _cookbook:

=======================================
Cookbook
=======================================


.. _cookbook-models:

Models
=============

Non editable model
--------------------

.. code-block:: python

    class MyModel(Part):

        @classmethod
        def excluded_modification_fields(cls):
            return cls().attributes


Condition on promotion
-------------------------

.. code-block:: python

    class MyModel(Part):

        def is_promotable(self):
            if condition_is_respected:
                return super(MyModel, self).is_promotable()
            else:
                return False


.. _cookbook-controllers:

Controllers
===============

Creation of a part using a controller
--------------------------------------

.. code-block:: python

   ctrl = PartController.create("Part_00011", "Part", "a", user, {"group":group})

.. _cookbook-tests:

Tests
==============

.. _cookbook-others:

Others
=============

Get next state of a PLMObject
-------------------------------

.. code-block:: python

    lcs = obj.lifecycle.to_states_list()
    next_state = lcs.next_state(obj.state.name)

.. seealso:: :meth:`.LifecycleList.next_state`


