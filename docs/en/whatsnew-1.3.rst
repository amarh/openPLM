.. _whatsnew-1.3:

.. Images come later, once you are sure you would not have to update them ;)

=========================
What's new in OpenPLM 1.3
=========================

.. warning::

    OpenPLM 1.3 is still in development, you can read the 
    :ref:`previous release notes <whatsnew-1.2>`.


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
    * 

What's new for users
=====================

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

.. figure:: /whatsnew/1.3/editor_compose.png
    :align: center

    The compose mode of the markdown editor.


.. figure:: /whatsnew/1.3/editor_preview.png
    :align: center

    The preview mode of the markdown editor.


.. figure:: /whatsnew/1.3/editor_result.png
    :align: center

    The rendered text.

Parts and documents: new *description* field
++++++++++++++++++++++++++++++++++++++++++++++

Parts and documents have now a *description* field.
Now parts, documents, groups and ECRs have a name and a description fields.

This field supports formatted content.


Assembly promotion in two clicks
+++++++++++++++++++++++++++++++++++

A new button is available to promote a whole assembly.
It is no more necessary to promote each individual part in the right order.

This button is available if the following conditions are met:

    * the user is the only signer of every parts (or other signers have delegated their right);
    * all leaf parts are attached to an official document.


Avatars
++++++++++++++++++


Check-in improvements
++++++++++++++++++++++

Search: all types
+++++++++++++++++++++++

Timeline: browse by date and filtering
++++++++++++++++++++++++++++++++++++++++++

Navigate: full screen display
++++++++++++++++++++++++++++++

3D view: full screen display and BOM
+++++++++++++++++++++++++++++++++++++


.. figure:: /whatsnew/1.3/3D_mendelmax.png
    :align: center
    
    The model is done by `Brojt <http://www.thingiverse.com/thing:19782>`_.
    It is licenced under the `Attribution - Share Alike - Creative Commons license`_. 

.. _Attribution - Share Alike - Creative Commons license: http://creativecommons.org/licenses/by-sa/3.0/


Other enhancements
++++++++++++++++++++++

What's new for administrators
===============================

:doc:`/admin/upgrade/upgrade-1.3`


Customize default references
+++++++++++++++++++++++++++++++++

It is now possible to customize the default reference of parts and document.
Read :ref:`admin-references` for details on how to customize default
references.

New application: richpage
+++++++++++++++++++++++++++++++++

:ref:`richpage-admin`


What's new for developers
===============================

Django 1.5
++++++++++++++

    * StreamingHttpResponse
    * static files

Call :func:`~user.profile` instead of ``user.get_profile()``.

Rich text | Wiki syntax
++++++++++++++++++++++++++

:ref:`devel-richtext`

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


References
++++++++++++

:mod:`.references`


Previous versions
=================

.. toctree::
    :maxdepth: 1

    whatsnew/whatsnew-1.2
    whatsnew/whatsnew-1.1

