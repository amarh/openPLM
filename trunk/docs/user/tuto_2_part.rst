========================================================
Functions related to PLMObject : **PART**
========================================================


This document describes the functions you can use to display and manipulate the **Parts** in openPLM.


OVERVIEW
========================================================
The **Parts** are PLMObjects. They represent a product in real life.

Eg : A bicycle, a pack of cookies, a medicine, a wheel, a cookie, some floor, some sugar, ...

**Part** is a subclass of PLMObject. Depending on the industry you use OpenPLM for, we can define subclasses of **Part**.
Each subclass are designated as *type*.

========================    ===============================     ===============================
Example 1 :                 Example 2:                          Example 3 : 
========================    ===============================     ===============================
PLMObject                   PLMObject                           PLMObject
...=> Part                  ...=> Part                          ...=> Part
......=> Bicycle            ......=> CardboardPacking           ......=> CardboardPacking
......=> Wheel              ......=> PlasticWrap                ......=> PlasticWrap
......=> Handlebar          ......=> Cake                       ......=> Syrup
......=> Saddle             ......=> Floor                      ......=> Sugar
......=> ...                ......=> ...                        ......=> ...
========================    ===============================     ===============================


In one subclass/type, you have several instances with a *reference*.

For a reference, you may have several *revisions* in order to trace the major modifications. They follow the a, b, c, ... sequence or 1, 2, 3, ... sequence or any other customized sequence.

Each **Part** have a unique set of *type*, *reference*, *revision*.

.. hint :: Example : Bicycle / BI-2010 / a

Assemblies and sub-assemblies are also Parts. We can create links between an assembly and another Part. Doing that we define the assembly and, therefore, build a BOM (Bill Of Material).

We can create links between a **Part** and **Documents**. Each Document helps the Part definition/description.


ATTRIBUTES
========================================================
Displays the ID card of the part.

You find standard attributes like name, date of creation, owner, ...
You find customized attributes depending of the company OpenPLM is implemented for (like size or weight or supplier, ...).

If you have necessary rights, you can **Edit** the attributes and modify them.

.. note :: You can proceed some research based on each attribute.


LIFECYCLE
========================================================
Displays the lifecycle of the part.

You find the different states of the part including the current one. These lifecycles can be customized following specifications given by the company OpenPLM is implemented for (with 1, 2, 3 or more states).

If you have necessary rights, you can **Promote** or **Demote** the part.

We can implement different triggers on **Promote**/**Demote** actions following specifications (rights checking, e-mail sending, other PLMObject promotion, ...).


REVISIONS
========================================================
Displays all the revisions of the part.

If the current part is the last revision, we can add a new one.


HISTORY
========================================================
Displays the history of the part.

It ensures the full tracability of the part.


MANAGEMENT
========================================================
Displays related Users and their rights on the part.

If you have necessary rights, you can **Replace** some Users. You can also add one or several Users for e-mail notification i.e. he/she will receive e-mail for each new event related to this part (revision, modification, promotion, ...).


BOM-CHILD
========================================================
Displays BOM of the current part i.e. Parts which are under or which are in.

You can filter *1 level* (only sons) or *all levels* (grandsons, great-gransons, ...) or *last level*. You can also specify a date in order to get the BOM at that time.

If you have necessary rights, you can **Add** a new Part/children specifying its type, reference, revision, its quantity (1, 2, 0.5 kg, 2.5 m, ...) and its ordering number (which define where the children is shown in the BOM).

If you have necessary rights, you can **Edit** the first level and modify quantity, ordering number or remove the Part out of the BOM.

PARENTS
========================================================
Displays Parts which are upon the current part.

You can filter *1 level* (only parents) or *all levels* (grandparents, great-grandparents, ...) or *last level*. You can also specify a date in order to see the assemblies where we could find the current part at that time.


DOC-CAD
========================================================
Displays related Documents of the current part.

If you have necessary rights, you can **Add** a new Document.

If you have necessary rights, you can **Remove** a Document. 

