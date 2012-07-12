=================================================================
Functions in common related PLM objects : **PART** / **DOCUMENT**
=================================================================

OVERVIEW
========================================================

The **Parts** and **Documents** are PLM objects. They represent a product in real life.

Eg : A bicycle, a pack of cookies, a medicine, a wheel, a drawing, a 3D document, ...

**Part** and **Document** are subclasses of **PLMObject**. Depending on the industry you use OpenPLM for, we can define subclasses of **Part** and **Document**.
Each subclass are designated as *type*.

========================    ===============================     ===============================
Example 1 :                 Example 2 :                         Example 3 :                    
========================    ===============================     ===============================
PLMObject                   PLMObject                           PLMObject                      
...=> Part                  ...=> Part                          ...=> Document                    
......=> Bicycle            ......=> CardboardPacking           ......=> Drawing      
......=> Wheel              ......=> PlasticWrap                ......=> Standard
......=> Handlebar          ......=> Cake                       ......=> TestData
......=> Saddle             ......=> Floor                      ......=> Document3D
......=> ...                ......=> ...                        ......=> ...
========================    ===============================     ===============================


In one subclass/type, you have several instances with a *reference*.

For a reference, you may have several *revisions* in order to trace the major modifications. They follow the a, b, c, ... sequence or 1, 2, 3, ... sequence or any other customized sequence.

Each **Part** and **Document** have a unique set of *type*, *reference*, *revision*.

.. hint :: Example : Bicycle / BI-2010 / a

Assemblies and sub-assemblies are also Parts. We can create links between an assembly and another Part. Doing that we define the assembly and, therefore, build a BOM (Bill Of Material).

We can create links between a **Part** and **Documents**. Each Document helps the Part definition/description.

Documents contain one or more electronic files. 


ATTRIBUTES
========================================================

Displays the ID card of the object.

You find standard attributes like name, date of creation, owner, ...
You find customized attributes depending of the company OpenPLM is implemented for (like size or weight or supplier, ...).

If you have necessary rights, you can :
  * **Edit** the attributes and modify them,
  * **Clone** the current object.

.. note :: You can proceed some research based on each attribute.


LIFECYCLE
========================================================

Displays :
 * the lifecycle of the object,
    
 * related users and their rights.

You find the different states of the object including the current one. 
These lifecycles can be customized following specifications given by 
the company OpenPLM is implemented for (with 1, 2, 3 or more states).

If you have necessary rights, you can :
 * **Promote** or **Demote** the object
    
 * **Cancel** the object

 * **Replace** some signers or notified users
    
 * **Add** or **Remove** Users for e-mail notification, i.e. he/she will receive e-mail 
   for each new event related to this object (revision, modification, promotion, ...).

We can implement different triggers on **Promote**/**Demote** actions 
following specifications (rights checking, e-mail sending, other PLM object promotion, ...).


REVISIONS
========================================================

Displays all the revisions of the object.

If the current object is the last revision, we can add a new one.


HISTORY
========================================================

Displays the history of the object.

It ensures the full tracability of the object.

A RSS feed icon is shown when you are on this tab. By clicking it you can
subscribe to the feed of the object.
