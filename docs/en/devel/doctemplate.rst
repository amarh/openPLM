=================================
Document templates
=================================

.. versionadded:: 2.1


Concept
=======

OpenPLM 2.1 introduces a new feature: document templates.

Templates are suggested at document creation.
If a template is selected, its files are copied when the document
is created.

Templates are documents. That means they have a lifecycle and they
are managed like other documents. They can be revised or deprecated.
In fact, templates are just documents with a special lifecycle.

Only official templates are suggested when a document is created.


Differences with cloning
-------------------------

It was already possible to duplicate a document by using the
clone feature.
But when a document is cloned, its attributes are copied.
If a template is cloned, the copied name and group would certainly be inaccurate.

Moreover, the template implies a different workflow.
A user starts by creating a document and it directly sees that it can use a template.


Forms
=====

:func:`.get_creation_form` adds a template field to a creation form if:

    * the type is a Document type which accepts file

This field is hidden if (one of the conditions):

    * the creation follows an upload (``pfiles`` parameter set)
    * no official templates of the given type exit
    * the *template* argument is set to ``False``

This is a :class:`ModelChoiceField` which accepts a null value.
      

Database implementation
=======================

Document model
--------------

The :class:`.Document` model has a new foreign key, :attr:`~.Document.template`
which identifies the template used at creation time.
This field can be null (the default).

Lifecycle
---------

A new type of lifecycle, :attr:`.Lifecycle.TEMPLATE` is available (database value: 4).

These lifecycles must have, at least, a draft, an official and a deprecated states




