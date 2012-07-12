========================================================
Main functions of openPLM
========================================================


This document describes the main concepts and the main functions of openPLM,
the first genuine open source PLM.


Requirements
=============

OpenPLM is a full web application i.e. you just need a web browser.
We advise you to use a decent browser, like Mozilla Firefox, 
Google Chrome, Opera or any browsers based on Webkit or Gecko.

In OpenPLM there are four main types of objects:

* User

* Group

* Part

* Document

The parts and documents are named according to the following convention:
*type//ref//rev//name*

    type
        refers to the type of the object (``Part``, ``Document``, ``Document3D``...)

    ref
        refers to the reference of the object (usually written as ``PART_1759`` or ``DOC_0051``)

    rev
        refers to the revision number of the object (``a``, ``1.2`` or ``A.a.1``...)

    name
        refers to the name of the object (may be empty)


.. _func-home:

Home page
========================================================

You have 5 main features:

1- Search for objects 

2- Navigate with link between objects

3- Creation of objects

4- Study an object (access to the object information)

5- Browse objects

Screenshot:

.. figure:: images/Capture_openPLM_home.png
    :width: 100%
    :align: center

    Home page


As shown on the example, your pending invitations (sent and received) are displayed on the home page.


.. _func-search:

Search
========================================================

The search block is divided in two blocks:

1- The search block where you enter your request

2- The block where results are displayed

First, you need to select the type of object you want to look for.

Then, you can fill the form if you want to refine your research with:

 * a set of words, OpenPLM will search for objects, of which attributes contains all the given words
 * advanced queries:
    * attribute=data 
        - ``name=test`` 
        - ``name:test``
    * attribute:data OR query
        - ``type=document3D OR type=design``
    * attribute:data AND query
        - ``name=test AND (type=document3D OR type=design)``

OpenPLM will highlight results according to the query.

Example:

.. figure:: images/Capture_openPLM_search.png
    :width: 100%
    :align: center    

    Search example

    As you can see, an empty query matches all objects.
    Here, all parts are returned, including their sub-types (here Assembly, SinglePart, RAM, ... ).


Navigate
========================================================
Objects and their links are represented in a graph.

Each box represent an object:

* Pink is for users

* Blue for parts

* Purple for documents

Example:

.. image:: images/Capture_openPLM_navigate.png
   :width: 100%


Create
========================================================

You can create an object by filling the form displayed.

Other ways to create objects are proposed under the form creation.

Example:

.. image:: images/Capture_openPLM_create.png
   :width: 100%


Study
========================================================

Reaching "Study" from the Home page shows the history of the objects related to the user.

The "Study" page contains tabs from where you can :

* access to informations of an object, user or group

* modify an object

Example:

.. figure:: images/Capture_openPLM_study.png
   :width: 100%
   
   Study
   
   The possible actions and displayed informations in "Study" view are describes here :
   
   * :ref:`en-plmObject-func`
   * :ref:`en-user-func`
   * :ref:`en-group-func`


Browse
======================================================

The "Browse" page displays all objects, groups and users available in your OpenPLM.
You can filter the results according to their type, status and you can change
the sorting order.

Example:

.. image:: images/Capture_openPLM_browse.png
   :width: 100%


Common Parts
=======================================================

**The header**

It contains:

    * User's name (if the user is logged)
    
    * Today's date and hour
    
    * Button to choose the language
    
    * Link to log out (or login)
    
    * Link to get help


**The toolbar**

    * Buttons to reach different views

    * A history of objects reached during your session

If you place your mouse over an object in the history, the corresponding menu will be shown.

Once you are logged in, the header and the toolbar appears in all views. 
Except in "Home" page, where only the header appears.

.. figure:: images/Capture_openPLM_header.png
   :width: 100%
   
   Header and toolbar


**The left panel**

It can be showed or hidden. This left panel is a search
area with the same structure as the SEARCH view described higher

Depending on the current object and the current page this panel can have extra functions.

This panel does not appear in the home page and the "Search" page.

.. image:: images/Capture_openPLM_leftpanel.png
   :width: 100%

