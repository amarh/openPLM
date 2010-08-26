=======================================
Cookbook
=======================================


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


Controllers
===============


Tests
==============

Others
=============

Get next state of a PLMObject
-------------------------------

.. code-block:: python

    lcs = obj.lifecycle.to_states_list()
    next_state = lcs.next_state(obj.state.name)

.. seealso:: :meth:`.LifecycleList.next_state`


