.. _whatsnew-1.1:

.. Images come later, once we are sure we would not have to update them ;)

=========================
What's new in OpenPLM 1.1
=========================

User changes
===============

New files uploading
-------------------



Browsing feature
------------------

A new feature is available to browse all parts, documents, groups and users.


Lifecycle and management
-------------------------

The lifecycle and management pages have been merged into the lifecycle page.

Replacing a signer is now much more intuitive.


Public pages
----------------

It is now possible to publish a part or a document. A published item is accessible to
anonymous users.


Restricted account and sponsoring
--------------------------------------

A new kind of account is available: restricted account.

A restricted account can not create any contents and can only access to selective 
parts and documents.

This new account make it possible to share some contents to someone and be sure he
would not be able to modify it or see other confidential data.

To create a restricted account, you only have to sponsor a new user and
select the "restricted account" option:

.. todo:: image

As you can see on the screenshot above, it is now possible to sponsor a
new use who can access mostly all contents but can not modify them.

RSS feeds
----------

New application: oerp
---------------------

document3D
-----------

The document3D application has been improved.

3D view enhancements
+++++++++++++++++++++


Highlighting
~~~~~~~~~~~~~~~

.. todo:: screenshots, gifs

Shading
~~~~~~~~~~

.. todo:: screenshots

View selection
~~~~~~~~~~~~~~

A new toolbar is available to switch between views (front, top...).

.. todo:: screenshots

Random colors and transparency
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. todo:: screenshots

STL 
++++++++++++++

The 3D view can now display STL files (ASCII and binary formats).


STEP file thumnnails
+++++++++++++++++++++

OpenPLM can now generate a thumbnail of a STEP file. Currently, only
non decomposed STEP files are handled.

.. todo:: example

WebDAV access
--------------

OpenPLM can now serves all managed files through a WebDAV access.

Bugs fixed
------------

Other enhancements
--------------------

BOM: download as PDF

BOM: replace child

Part and document cancellation

Display enhancements:
Groups, revisions...

Search panel: asynchronous

Documentation: 

    * More documented features
    * disponible dans la langue de Molière


Thumbnails: new supported formats
SolidWorks, Catia, Sketch Up, Pro Engineer 


Administrator changes
=======================

Restricted accounts and publishers
-----------------------------------

Applications layout
-------------------

A big change has been made to the application layout. Optionnals applications
are now located in the apps folder.

Make sure that your settings.py file has been update in consequences : 
with the exception of plmapp, openPLM applications are now noted openPLM.apps.AppliName

exemple : 

'openPLM.plmapp',
'openPLM.apps.cad',
'openPLM.apps.cae',
'openPLM.apps.office',

document3D
-----------

New optional dependency: povray

New application: oerp
----------------------

Developer changes
==================


