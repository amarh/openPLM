.. _whatsnew-2.0:

.. Images come later, once you are sure you would not have to update them ;)

=========================
What's new in OpenPLM 2.0
=========================


Introduction
===============


OpenPLM is a product oriented PLM solution.
A product oriented PLM (Product Lifecycle Management) solution unifies
all activities of the company in an ECM which structures data around the product.
OpenPLM features a full web and user-friendly interface. 
OpenPLM is Free and Open Source Software.
This means that all our work is free to use, modify and redistribute. 

Notable changes:

    * Wiki syntax and Page document
    * Avatars
    * Interface enhancements 

What's new for users
=====================

Enhanced Login page
+++++++++++++++++++
We improve the style of the Login page.

.. image:: /whatsnew/2.0/login_page.png
    :align: center

Enhanced Home page
+++++++++++++++++++
You access to Search engine directly from Home page.

.. image:: /whatsnew/2.0/home_page.png
    :align: center


Wiki syntax
++++++++++++++++++

It is now possible to write rich formatted comments and other text
(description, technical details, etc.).

The syntax is based on Markdown and it supports:

    * titles and subtitles
    * images
    * bullet and ordered lists
    * tables
    * special links (to a part, document, user and more)

The syntax is documented :ref:`on this page <user-richtext>`.

A visual editor is available:

.. figure:: /whatsnew/2.0/editor_compose.png
    :align: center

    The compose mode of the markdown editor.


.. figure:: /whatsnew/2.0/editor_preview.png
    :align: center

    The preview mode of the markdown editor.


.. figure:: /whatsnew/2.0/editor_result.png
    :align: center

    The rendered content.

Interface enhancements
+++++++++++++++++++++++

All buttons have been redesigned.
Their background colors depend on the consequences of their actions.
For example, delete buttons have a red background and promote buttons
have a green background.

.. figure:: /whatsnew/2.0/attributes.png
    :align: center

    Icons and styles are based on Twitter Bootstrap.

.. figure:: /whatsnew/2.0/toolbar.png
    :align: center

    The main toolbar

.. figure:: /whatsnew/2.0/cards.png
    :align: center

    New cards


Parts and documents: new *description* field
++++++++++++++++++++++++++++++++++++++++++++++

Parts and documents have now a *description* field.
Now parts, documents, groups and ECRs have a name and a description fields.

This field supports formatted content and is indexed by the search engine.


Assembly promotion in two clicks
+++++++++++++++++++++++++++++++++++

A new button is available to promote a whole assembly.
It is no more necessary to promote each individual part in the right order.

This button is available if the following conditions are met:

    * the user is the only signer of every parts (or other signers have delegated their right);
    * all leaf parts are attached to an official document.


Avatars
++++++++++++++++++

Each user can now upload an avatar.

Avatars are visible on:

    * each user's page

      .. image:: /whatsnew/2.0/avatar_profile.png

    * each comment

      .. image:: /whatsnew/2.0/avatar_comment.png

    * each action of the timeline

    
      .. image:: /whatsnew/2.0/avatar_timeline.png

    * each card (browse and navigate)
      
      .. image:: /whatsnew/2.0/avatar_card.png


To upload your avatar, simply edit your personal data on your user's page.


Check-in improvements
++++++++++++++++++++++

A click on the check-in button immediately triggers the file selector.
And the file is uploaded when the file selector is validated.


Search: all types, official objects
++++++++++++++++++++++++++++++++++++

It is possible to run a query matching any types of object (parts, documents,
groups, users, ECRs).

The drop down menu used to select the type is replaced by a left panel.
This panel is divised in two sections. The first section gives
direct access to main types (All, Part, Document, Group, User and ECR).
The second is fold and gives access to part or document subtypes
(Document3D, ElectronicPart, etc.).

It is possible to search for only official objects.

Moreover, the search engine suggests a spelling correction when no results
are returned.

Timeline: browse by date and filtering
++++++++++++++++++++++++++++++++++++++++++

The timeline has been improved. It now displays all events which happened
during a given period. 
The previous version displayed a fixed number of events.

Moreover, it is possible to filter events based on their type (part, document and/or group)
and by their author.


.. figure:: /whatsnew/2.0/history.png
    :align: center

    History of a part

Navigate: full screen display
++++++++++++++++++++++++++++++

You can now display the navigate view in full screen mode.


3D view: full screen display and BOM
+++++++++++++++++++++++++++++++++++++

The assembly tree of a STEP file is now displayed as a treeview.

You can now display the 3D view in full screen mode.
 

.. figure:: /whatsnew/2.0/3D_mendelmax.png
    :align: center
    
    The model is done by `Brojt <http://www.thingiverse.com/thing:19782>`_.
    It is licenced under the `Attribution - Share Alike - Creative Commons license`_. 

.. _Attribution - Share Alike - Creative Commons license: http://creativecommons.org/licenses/by-sa/3.0/


Other enhancements
++++++++++++++++++++++

    * The Document3D type is automatically selected if a CAD file is uploaded
    * Navigate supports ECRs
    * The :ref:`webdav application <webdav-admin>` is now compatible with Windows 7 client
    * All comments have a permalink
    * Histories and timeline record comments

    

What's new for administrators
===============================

OpenPLM now requires Django 1.5. 
Some dependencies and the settings file must be upgraded.
Read the :doc:`instructions </admin/upgrade/upgrade-2.0>` before upgrading
your installation.


Customize default references
+++++++++++++++++++++++++++++++++

It is now possible to customize the default reference of parts and documents.
Read :ref:`admin-references` for details on how to customize default
references.

New application: richpage
+++++++++++++++++++++++++++++++++

The :ref:`richpage application <richpage-admin>` adds a new type
of document, *Page* which has a dedicated tab to a formatted content.



What's new for developers
===============================

Django 1.5
++++++++++++++

Django 1.5 adds *custom user model*. OpenPLM still uses the User model
provided by Django and a separated profile (:class:`~UserProfile`).
To get the profile of a user instance, you must now access the
:samp:`{user}.profile` attribute instead of calling :samp:`{user}.get_profile()`.


Static files are now located in :samp:`{app}/static/` directories
instead of the `media/` directory.

HttpResponse which takes a file or an iterator are now
instances of :class:`.StreamingHttpResponse`.

All DateTime fields are now timezone aware.


Rich text | Wiki syntax
++++++++++++++++++++++++++

You can now add rich text support to any TextField.
:ref:`devel-richtext` explains how to add this support and how
to add its own syntax.

Modules
++++++++++++

:mod:`plmapp.utils` is now a package and the modules :mod:`.archive`,
:mod:`.encoding`, :mod:`.unicodecsv`, :mod:`.units` moved to this package.

A new module, :mod:`plmapp.utils.importing` is available to import a function
or a class from a string. It is based on the one provided by Mezzanine.

:mod:`plmapp.base_views` moved to :mod:`plmapp.views.base`.

A lot of views moved from :mod:`plmapp.views.main` to :mod:`plmapp.views.group`,
:mod:`plmapp.views.document`, :mod:`plmapp.views.part`,
:mod:`plmapp.views.plmobject` or :mod:`plmapp.views.user`.

HTTP API
++++++++

The :mod:`http_api` has new routes:

    - :func:`http_api.get`
    - :func:`http_api.attached_documents`
    - :func:`http_api.attached_parts`
    - :func:`http_api.lock_files`


References
++++++++++++

The new module :mod:`.references` adds functions to parse and generate
a new reference for a part or a document.

Celery tasks
++++++++++++++++

Task are now executed after the current database transaction.
If the transaction failed, tasks are not executed.

Models
+++++++

:class:`.PLMObject` has now a :attr:`~.PLMObject.description` field.
If one of your models already has a such field, you should create
a migration *before* upgrading your installation. The software
application contains a migration that copies the content
of an existing description field.


Document subclasses may implement the :meth:`.Document.get_creation_score`
classmethod. It is used to determinate which document type is chosen
after an upload.

Previous versions
=================

.. toctree::
    :maxdepth: 1

    whatsnew/whatsnew-1.2
    whatsnew/whatsnew-1.1

