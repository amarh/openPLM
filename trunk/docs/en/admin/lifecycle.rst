===============
Lifecycle
===============


Adding a new lifecycle
========================

A lifecycle must have at least 3 states:

    1. a draft state
    #. optional states
    #. an official state
    #. a deprecated state 

Using the admin interface
++++++++++++++++++++++++++++

First, you need to create all states: open the page
:samp:`http://{server}/admin/plmapp/state/add` and create them. The only
required field is the name of the state, this value will be displayed in the
lifecycle page. It's fine if a state is referred by several lifecycles.

Then you need to create a lifecycle: open the page
:samp:`http://{server}/admin/plmapp/lifecycle/add/` and create it.
Two fields are required: its name (that will be shown in the creation page)
and its official state.

Then you need to create objects (named lifecyclestates) that bound the states
to the lifecycle.  Open the page
:samp:`http://{server}/admin/plmapp/lifecyclestates/add/` and create one object
per state. Three fields are required:

    1. The lifecycle
    2. The state
    3. A rank: this field (an integer) is used to order the states,
       the first state must have the lower rank.

Using the python shell
++++++++++++++++++++++++++++


It is possible to programamtically create a lifecycle.

Open a python shell (:command:`./manage.py shell`):

    >>> from openPLM.plmapp.models import Lifecycle
    >>> from openPLM.plmapp.lifecycle import LifecycleList
    >>> # arguments: name of the lifecycle, name of the official state, names off all states (ordered) 
    >>> lcl = LifecycleList("mylifecycle", "official", "draft", "state2", "state3", "official", "deprecated")
    >>> Lifecycle.from_lifecyclelist(lcl) # create the lifecycle
    <Lifecycle: Lifecycle<mylifecycle>>

.. seealso:: :class:`.LifecycleList`


How to change the lifecycle of an object
===========================================

If you have to change the lifecycle of an object, you have to:
    
    1. Edit its PLMObject page (via the admin interface):
       make sure its state is consistent with the new lifecycle

    2. Make sure there is one (not least, not more) signer assigned to each signing level
       (number of states minus one levels):
       Add/edit required :class:`PLMObjectUserLink` (:samp:`http://{server}/plmapp/plmobjectuserlink/`).
       All missing roles must start with ``sign_``.

.. note::

    If you have to select a signer role above 10, you will have to edit
    the code of :file:`plmapp/models.py`, find the following lines::
                
        ROLES = [ROLE_OWNER, ROLE_NOTIFIED, ROLE_SPONSOR]
        for i in range(10): # increase this number
            level = level_to_sign_str(i)
            ROLES.append(level)
        ROLE_READER = "reader"

    increase the number 10 and restart your server.

    (Yes, its annoying, but you should not change the lifecycle of an object).


           

