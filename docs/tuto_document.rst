========================================================
Functions related to PLMObject : **DOCUMENT**
========================================================


This document describes the functions you can use to display and manipulate the **Documents** in openPLM.


OVERVIEW
========================================================
The **Documents** are PLMObjects. They contain files (.txt, .jpg, .odt, .doc, .xls, ...).

Eg : A drawing, a quality report, a customer specification, a 3D model, ...

**Document** is a subclass of PLMObject. Depending on the company you use OpenPLM for, we can define subclasses of **Documents**.
Each subclass are designated as *type*.

**Example :**

|    PLMObject
|    ...=> Document
|    ......=> Drawing
|    ......=> Standards
|    ......=> TestData
|    ......=> TestReport
|    ......=> QualityIncident
|    ......=> QualityActionPlan
|    ......=> OperatingMode
|    ......=> CustomerSpecification
|    ......=> ...


In one subclass/type, you have several instances with a *reference*.

For a reference, you may have several *revisions* in order to trace the major modifications. They follow the a, b, c, ... sequence or 1, 2, 3, ... sequence or any other customized sequence.

Each **Document** have a unique set of *type*, *reference*, *revision*.

.. hint :: Example : QualityActionPlan / QAP-0011 / 1

We can create links between a **Document** and **Parts**. Documents help the Part definition/description.

Documents contain one or more electronic files. 


ATTRIBUTES
========================================================
Displays the ID card of the document.

You find standard attributes like name, date of creation, owner, ...
You find customized attributes depending of the company OpenPLM is implemented for (like number of pages, format, ...).

If you have necessary rights, you can **Edit** the attributes and modify them.

.. note :: You can proceed some research based on each attribute.


LIFECYCLE
========================================================
Displays the lifecycle of the document.

You find the different states of the document including the current one. These lifecycles can be customized following specifications given by the company OpenPLM is implemented for (with 1, 2, 3 or more states).

If you have necessary rights, you can **Promote** or **Demote** the document.

We can implement different triggers on **Promote**/**Demote** actions following specifications (rights checking, e-mail sending, other PLMObject promotion, ...).


REVISIONS
========================================================
Displays all the revisions of the document.

If the current part is the last revision, we can add a new one.


HISTORY
========================================================
Displays the history of the document.

It ensures the full tracability of the document.


MANAGEMENT
========================================================
Displays related Users and their rights on the document.

If you have necessary rights, you can **Replace** some Users. You can also add one or several Users for e-mail notification i.e. he/she will receive e-mail for each new event related to this document (revision, modification, promotion, ...).


PARTS
========================================================
Displays related Parts of the current document.

If you have necessary rights, you can **Add** a new Part.

If you have necessary rights, you can **Remove** a Part. 


FILES
========================================================
Displays files uploaded in the current document.

You can :
    * if you have necessary rights, add/upload files
    * simply download them
    * if you have necessary rights, you can check-out them (download and lock file)
    * if you have necessary rights, you can check-in them (upload and unlock them).

