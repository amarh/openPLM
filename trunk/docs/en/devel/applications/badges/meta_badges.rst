=================================================
:mod:`badges.meta_badges` --- badges 
=================================================

This module contains all available badges and their condition.


MetaBadge
==================

All badges are subclassed from :class:`MetaBadge` .

.. autoclass:: openPLM.apps.badges.utils.MetaBadge
    :members:

    
How to add a new badge
=======================

To add a new badge, create the class corresponding to its in the file :file:`meta_badges.py`.

Here's how was added the Autobiographer badge.


Fields
----------------

Some fields in your badge class are required see below.
This fields need to be set so the badge can be identified and displayed.


.. literalinclude:: autobiographer.py
    :linenos:
    :end-before: not required
    
    
Functions
-------------------- 

:func:`get_progress()`
++++++++++++++++++++++

The value returned by :func:`get_progress()` will be used to calculate the percentage of progress (see :class:`openPLM.apps.badges.utils.MetaBadge`).

.. literalinclude:: autobiographer.py
    :linenos:
    :start-after: required functions


Optional functions  
+++++++++++++++++++

.. literalinclude:: autobiographer.py
    :linenos:
    :start-after: optional functions
    :end-before: required functions
    
The :func:`get_user` function may need to be overriden for some badges.

The functions which name begins by *check* are used to check if the
user (of the instance) can win the badge.
You may not need to define more check functions.


The complete Autobiographer class 
----------------------------------------

.. literalinclude:: autobiographer.py
    :linenos:
