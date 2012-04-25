========================================================
Main functions of openPLM
========================================================


This document describes the main concepts and the main functions of openPLM,
the first genuine open source PLM.


REQUIREMENTS
=============

OpenPLM is a full web application i.e. you just need a browser.
We advise you Mozilla Firefox 3.6.

In OpenPLM there are four main types of objects :

* User

* Group

* Part

* Document

The parts and documents are named according to the following convention :
*type//ref//rev//name*

* *type* refer to the type of the object

* *ref* refer to the reference of the object (usually write as type_number)

* *rev* refer to the number revision of the object

* *name* refer to the name of the object ifs has been given a name


HOME PAGE
========================================================
You have 4 main features:

1- Search for objects 

2- Navigate with link between objects

3- Creation of objects

4- Study an object (access to the object information)

Example :

.. image:: images/Capture_openPLM_home.png
   :width: 100%

As shown on the example, your pending invitations (sent and received) are displayed on the home page.


SEARCH
========================================================
The search block is part in two :

1- The search part where you will enter your request

2- The part where the result will be display

First, you need to select the type of PLMObject you want to look for.

Then, you can fill the form if you want to refine your research.

OpenPLM will display the attributes which correspond to this type.

Example :

.. image:: images/Capture_openPLM_search.png
   :width: 100%


NAVIGATE
========================================================
Objects and their links are represented in a graph.

Each box represent an object :

* Pink is for users

* Blue for parts

* Purple for documents

Example :

.. image:: images/Capture_openPLM_navigate.png
   :width: 100%


CREATE
========================================================
You can create an object filling the form displayed.

Others ways to create objects are proposed under the form creation.

Example :

.. image:: images/Capture_openPLM_create.png
   :width: 100%


STUDY
========================================================
Reaching "Study" from the Home page show the history of the objects related to the user.

On the "Study" page you can :

* display informations of an object

* reach and modify an object

Example :

.. image:: images/Capture_openPLM_study.png
   :width: 100%


COMMON PARTS
=======================================================
No matter the chosen function (search,create,study or navigate),
two parts are common to all views :

1- The header which contains :

    * User's name, the day, a button to choose the language and a button to log out

    * Button to reach different views

    * A history of objects reached during your session

If you place your mouse over an object in the history, the corresponding menu will be shown.

.. image:: images/Capture_openPLM_header.png
   :width: 100%

2- The left panel that can be showed or hidden. This left panel is a search
area with the same structure as the SEARCH view described higher

Depending on the current object and the current page this panel can have extra functions.

.. image:: images/Capture_openPLM_leftpanel.png
   :width: 100%

