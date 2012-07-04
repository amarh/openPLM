========================================================
Functions related to : **USER**
========================================================


This document describes the functions you can use to display and manipulate the **Users** in openPLM.


OVERVIEW
========================================================
The **Users** are standard Django objects. With OpenPLM you can modify some attributes, change your password and delegate your rights.

In OpenPLM, the *type* is **User**.

In **User** class, you have several instances with a *username*.

Each **Users** have a unique *username*.

.. hint :: Example : User / pdurand / -

We can create links between a **User** and **Parts** or **Documents**. These Links define different rights **Users** have on each **Part** and each **Document**.

We can create delegation links between the **Users** in order to allow rights transfer. 


ATTRIBUTES
========================================================
Displays the ID card of the user.

You find standard attributes like first name, last name, e-mail adress, date of creation, ...
You find customized attributes depending of the company OpenPLM is implemented for.

If you have necessary rights, you can **Edit** the attributes and modify them.

If you have necessary rights, you can  change the **Password**.

.. note :: You can proceed some research based on each attribute.


HISTORY
========================================================
Displays the history of the user.

It ensures the full tracability of the user.


PARTS-DOC-CAD
========================================================
Displays related Parts and Documents of the current user.


DELEGATION
========================================================
Display Users delegated by the current user and their assigned roles.

If you have necessary rights, you can :
  * **Add** some delegated Users for each role.

  * **Stop** delegation.


GROUPS
========================================================
Displays related Groups of the user.

