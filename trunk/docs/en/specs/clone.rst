.. _clone-spec:

===================================================
Part and document cloning: specifications
===================================================

This document describes which parts and documents can be cloned,
which data are copied and how an user should be able to clone
a part.


Permissions
===============

A user who is a contributor and who can read (access to the attributes pages)
can clone a part or a document.


Cloneable elements
===================

All parts and documents may be cloned. Their state and lifecycle do not matter:
even a cancelled object may be cloned.

A new property :attr:`.PLMObject.is_cloneable` is available and returns True
if the PLMObject can be cloned.
The implementation of this property by :class:`.PLMObject` must returns True.
A custom part or document may override this property to exclude some plmobjects
from the cloning process.

All users and groups can **NOT** be cloned.
All other data can not be cloned.

Cloning process
==================

Cloning button
-----------------

A clone button can appear on the attributes page after the "Download as PDF" button.

This clone button appears if:

    * the current user is a contributor
    * the current user can read this object
    * the call to :attr:`.PLMObject.is_cloneable` on the current object returns True

A click on this clone button redirects to the URL
:samp:`/object/{type}/{reference}/{revision}/clone/`.

Cloning page
---------------

The cloning page handles the URL :samp:`/object/{type}/{reference}/{revision}/clone/`

It must raises a :exc:`.PermissionError` if the user is not a contributor or
can not read the object.

This page is not accessible to a restricted account.

This page must show at the beginning a message explaining that the current
object will be cloned.

Then it should put a creation form filled and a form to select 
Document-Part links and Parent-Child links which will be cloned.


Creation form
++++++++++++++++

A creation form must be filled to clone a plmobject.

The type of this creation form is the type of the cloned plmobject.
The user must not be able to change this type.

This form must have a new reference.

The revision field must be set to the default new revision.

The lifecycle field should be set to the original lifecycle if it is not the
"cancelled" lifecycle. If the cloned plmobject is cancelled, the lifecycle field
must be set to the default lifecycle.
The user may change this lifecycle to a "normal" lifecycle (not cancelled).

If the user belongs to the plmobject's group, the group field must be set to the
original group.
If the user does not belong to the plmobject's group, the group field must be unset.
Available group choices are the groups the user belongs to.

All other creation fields (name, description...) are set from the cloned object.


Links forms
++++++++++++++++

The second part of the cloning page contains forms to select which plmobjects links
should be copied.

Parts
~~~~~~~

If the cloned plmobject is a part, two forms (formsets) are available:

    1. A form to select which documents will be attached to the new part.
       This form should suggest documents suggested while revising a part
       (documents returned by :meth:`.PartController.get_suggested_documents`.

    2. A form to select which children are added to the new part.
       This form should suggest children suggested while revising a part
       (current children as returned by :meth:`.PartController.get_children`
       
A part cloning must not change current parent-child links, it must only
create new links. 
So it should not modify links where the cloned part is the child.

Documents
~~~~~~~~~~~


If the cloned plmobject is a document, one form (formset) is available:

    1. A form to select which parts will be attached to the new documents.
       This form should suggest parts suggested while revising a document
       (parts returned by :meth:`.DocumentController.get_suggested_parts`.


Object creation
----------------

Once the user click on the create button, a new PLMObject is create
using the controller associated to the object's type.

The owner and creator field are set to the current user.
The dates of creation and last modification are the current date.

Other fields are set according to the creation form.

The state of the created object is the first state of its lifecycle.

The signers are not copied, they are set like if the object was simply
created.

Notification links are not copied.

Revision links are not copied.

Parts-documents links and Document-parts link are copied according
to the links forms.

If the cloned plmobject is a document, all non deprecated files are copied,
including their thumbnail, original filename and size.

Errors handling
----------------

If the creation form is invalid, the object must not be created and
the cloning page must be reloaded with all errors notified.

If an error happens while creating the links, the object must be deleted
(or the database creation must be rollback) and all created files must be deleted.
The creation page must be reloaded with an error message explaining that something
wrong happens.


Implementation
---------------

The cloning process must be implemented by a new method
:meth:`.PLMObjectController.clone` whose signature is overridden by
:class:`.PartController` and :class:`.DocumentController` to handle 
links creation and errors recovery.


