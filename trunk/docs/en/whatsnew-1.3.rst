.. _whatsnew-1.3:

.. Images come later, once you are sure you would not have to update them ;)

=========================
What's new in OpenPLM 1.3
=========================

.. warning::

    OpenPLM 1.3 is still in development, you can read the 
    :ref`whatsnew-1.2 <previous release notes>`.


Introduction
===============


OpenPLM is a product oriented PLM solution.
A product oriented PLM (Product Lifecycle Management) solution unifies
all activities of the company in an ECM which structures data around the product.
OpenPLM features a full web and user-friendly interface. 
OpenPLM is Free and Open Source Software.
This means that all our work is free to use, modify and redistribute. 

Notable changes:

    * Wiki syntax

What's new for users
=====================

What's new for administrators
===============================

:doc:`/admin/upgrade/upgrade-1.3`


Customize default references
+++++++++++++++++++++++++++++++++

It is now possible to customize the default reference of parts and document.
Read :ref:`admin-references` for details on how to customize default
references.


What's new for developers
===============================

Django 1.5
++++++++++++++

    * StreamingHttpResponse
    * static files

Call :func:`~models.user.get_profile` instead of ``user.get_profile()``.

Rich text | Wiki syntax
++++++++++++++++++++++++++

:ref:`devel-richtext`

Modules
++++++++++++

:mod:`plmapp.utils` is now a package and the modules :mod:`.archive`,
:mod:`.encoding`, :mod:`.unicodecsv`, :mod:`.units` moved to this package.

A new module, :mod:`plmapp.utils.importing` is available to import a function
or a class from a string. It is based on the one provided by Mezzanine.

References
++++++++++++

:mod:`.references`


Previous versions
=================

.. toctree::
    :maxdepth: 1
    :glob:

    whatsnew/*
