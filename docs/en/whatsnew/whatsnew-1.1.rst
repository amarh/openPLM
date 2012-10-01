.. _whatsnew-1.1:

.. Images come later, once we are sure we would not have to update them ;)


===========================
What's new in OpenPLM 1.1
===========================

###########################
What's new in OpenPLM 1.1.1
###########################

This release fixes a XSS security issue inside the template
:file:`templates/blocks/reference.html` where the name of
the current part/document was not escaped.

#########################
What's new in OpenPLM 1.1
#########################

User changes
===============

New files uploading
-------------------

You can now upload your files and keep an eye on the list of your files.

Multiple files upload is available:
you can select more than one file to upload.

Progress-bars appear while uploading files:
  * one per files

  * one for the total progress


Screenshots:

.. list-table::

    * - .. figure:: /whatsnew/1.1/Capture_openPLM_file_add.png
           :width: 100%

           New "Files" page
    
           As you can see, the upload form and the list of files are both displayed on the "Files" page.


    * - .. figure:: /whatsnew/1.1/Capture_openPLM_file_progress.png
           :width: 100%
               
           Progress-bars
           
           Now OpenPLM display progress informations for each uploaded file. A global progress information is also given.
    


Browsing feature
------------------

A new feature is available to browse all parts, documents, groups and users.

For more details see :ref:`feat-browse` feature documentation


Lifecycle and management
-------------------------

The lifecycle and management pages have been merged into the lifecycle page.

Replacing a signer is now much more intuitive, see the screenshot:

.. image:: /whatsnew/1.1/Capture_openPLM_lifecycle_management.png



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
select the "restricted account" option.

Screenshot:

.. image:: /whatsnew/1.1/Capture_openPLM_sponsor.png


As you can see on the screenshot above, it is now possible to sponsor a
new user who can access mostly all contents but can not modify them.

You can also select a language, the "new account" mail sent should be translated 
according to the chosen language.


Timeline
---------

The timeline is like a global history which contains:

 * all history events related to official objects
 * all history events related to objects owned by groups you are in
 

RSS feeds
----------

You can now subscribe to rss feeds for:

 * PLM objects
 * User
 * Group
 * the timeline

You can subscribre to these feeds from:

 * "History" pages
 * "Timeline" page

This feeds are updated when there is a change on the related object(s), user or group.


New application: oerp
---------------------

If you use OpenERP , OpenPLM provides a new application to "push" your official
parts (and their BOM) into OpenERP.

Document3D
-----------

The document3D application has been improved.

3D view enhancements
+++++++++++++++++++++


Highlighting
~~~~~~~~~~~~~~~

You can highlight a sub-assembly by moving your mouse over the sub-assembly name as show on 
the screenshot below:

.. figure:: /whatsnew/1.1/3D3.png
    
    Highlithing
    
    The highlighted part , L-Bracket, is displayed in red instead of green.


Shading
~~~~~~~~~~

Now there are shades displayed for 3D view.

Screenshots before and now:

.. list-table::

   * - .. figure:: /whatsnew/1.1/3D_old.png
            :width: 60%
            
            Before   
            
            
     - .. figure:: /whatsnew/1.1/3D1.png
            :width: 70%
            
            Now
        

View selection
~~~~~~~~~~~~~~

A new toolbar is available to switch between views (axometric, front, right, top, rear, left, bottom).


Random colors and transparency
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can switch between random colors or initial colors.
You can also toggle (enable/disable) the transparency and chose to display or hide axis.


.. figure:: /whatsnew/1.1/3D2.png
    :target: http://www.openplm.org/example3D/mendelmax2.html
    
    3D view new toolbars
    
    Click on it to test the new toolbars (view selection, random colors and transparency).
    
    
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

.. figure:: /whatsnew/1.1/webdav_nautilus.png

    A directory listing using Nautilus.


Bugs fixed
------------

**Suggested reference for PLM objects**

`108 <http://wiki.openplm.org/trac/ticket/108>`_ step management - Suggested part references are all the same

`113 <http://wiki.openplm.org/trac/ticket/113>`_  Part - Suggested reference may cause some problem

`117 <http://wiki.openplm.org/trac/ticket/117>`_ Object creation - If you update the page suggested reference and reference change


**BOM**

`121 <http://wiki.openplm.org/trac/ticket/121>`_ BOM - Display last level is not correct


**Document3D**

`104 <http://wiki.openplm.org/trac/ticket/104>`_ 3D data not copied when a Document3D is revised

`106 <http://wiki.openplm.org/trac/ticket/106>`_ document3D: can not decompose a step file defining two products with the same name


**File management**

`124 <http://wiki.openplm.org/trac/ticket/124>`_ File check-in broken


**Sponsorship**

`109 <http://wiki.openplm.org/trac/ticket/109>`_ Sponsorship - Character ' is authorised for username and leads to a bug


**Delegation**

`119 <http://wiki.openplm.org/trac/ticket/119>`_ Delegation - We can delegate someone who is not in the same groupe as the object


Other enhancements
--------------------

**BOM** 

 * download as PDF,
 * replace child.

**Navigate view**

If the current object is a part you can:

 * attach a new document,
 * add a new part (child).
 
If the current object is a document you can:

 * attach a new part.


**Part and document**

You can cancel and clone PLM objects.


**Search panel**

The research is performed asynchronously


**Display enhancements**

 * groups tab
 * revisions tab
 * ...
 
 
**Documentation** 

    * More documented features
    * disponible dans la langue de Molière


**Thumbnails: new supported formats**

SolidWorks, Catia, Sketch Up, Pro Engineer 


Administrator changes
=======================

Restricted accounts and publishers
-----------------------------------

Restricted accounts represent a user with the ``restricted`` field set to true.
A user with restricted access can:

 * neither be a contributor ( imply he(she) can't create object or group, sponsor user) neither an administrator
 * not be member of a group
 
A publisher is a user with the ``can_publish`` field set to true. He(she) can publish
all official PLM objects he(she) can read. A published object is accessible to everyone,
even anonymous users.

The ``restricted`` and ``can_publish`` fields can be set via the admin interface.
For more informations see :ref:`rest-account-specs` and :ref:`publication-specs`.



Applications layout
-------------------

A big change has been made to the application layout. Optionnals applications
are now located in the apps folder.

Make sure that your settings.py file has been update in consequences: 
with the exception of plmapp, openPLM applications are now named :samp:`openPLM.apps.{ApplicationName}`

Example:: 

    'openPLM.plmapp',
    'openPLM.apps.cad',
    'openPLM.apps.cae',
    'openPLM.apps.office',

New optional dependency
-------------------------

:command:`gsf` (package ``libgsf-bin`` in Debian/Ubuntu) is now used to generate a thumnail from a SolidWorks file.

document3D
-----------

New optional dependency: povray

New application: oerp
----------------------

This application depends on oerplib and require an update of your setting.py file, see :ref:`oerp-admin`.


Developer changes
==================

New applications
-----------------

Some new applications were implemented, more details in :ref:`applications`.

Library changes
----------------

:mod:`openPLM.plmapp.models`
+++++++++++++++++++++++++++++++

    * :attr:`.UserProfile.can_publish`: added: True if user can publish a plmobject
    * :attr:`.UserProfile.restricted`: added: True if user has a restricted account
    * :attr:`.PLMObject.published`: added.
    * :attr:`.PLMObject.reference_number`: added.
    * :attr:`.PLMObject.is_cloneable`: added.
    * :attr:`.PLMObject.published_attributes`: added.

:mod:`plmapp.controllers.plmobject`
++++++++++++++++++++++++++++++++++++++++

    * :meth:`.PLMObjectController.check_publish`: added.
    * :meth:`.PLMObjectController.can_publish`: added.
    * :meth:`.PLMObjectController.publish`: added.
    * :meth:`.PLMObjectController.check_unpublish`: added.
    * :meth:`.PLMObjectController.can_unpublish`: added.
    * :meth:`.PLMObjectController.unpublish`: added.
    * :meth:`.PLMObjectController.check_cancel`: added.
    * :meth:`.PLMObjectController.can_cancel`: added.
    * :meth:`.PLMObjectController.check_clone`: added.
    * :meth:`.PLMObjectController.can_clone`: added.
    * :meth:`.PLMObjectController.clone`: added.

New modules
+++++++++++

    * :mod:`plmapp.thumbnailers.jfifthumbnailer`
    * :mod:`plmapp.thumbnailers.pngthumbnailer`
    * :mod:`plmapp.thumbnailers.swthumbnailer`

The modules ``plmapp.native_file_management`` and ``plmapp.cadformats`` have been merged
into a new module: :mod:`plmapp.fileformats`.

:mod:`plmapp.units`
++++++++++++++++++++++++

    * :exc:`.UnitConversionError`: added.
    * :func:`.convert_unit`: added.

:mod:`plmapp.utils`
+++++++++++++++++++++++

    * :class:`.SeekedFile`: added.
    * :func:`.get_ext`: added.
    * :func:`.get_pages_num`: added.

