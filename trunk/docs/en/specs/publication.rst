.. _publication-specs:

=================================
Publication
=================================

.. versionadded:: 1.1


This document defines how a part or a document can be published to
be accessible to anonymous user.


Condition to publish a part or a document
=========================================


A part or a document can be publish if and only if it is official.

Only an user who belongs to the object's group and who has the
permission right to published an object can publish an object.
The *permission right* can be set via the admin interface.

An user who can publish a plmobject is a *publisher*.

The interface should ask a confirmation and the user's password before
publishing a plmobject. This confirmation dialog should warn about the
main consequence of a publication: a publish part or document is fully
accessible to everyone, including anonymous users.


Access
======

A published plmobject can be accessed by all users, including
anonymous users.

The URL to access a published object must follow the following pattern:

    * :samp:`/object/{type}/{reference}/{revision}/public/`

An anonymous access to an unpublished object must redirect to the login page.

Visible data
==============


The public page of a **part** shows the following data:

    * its type
    * its reference
    * its revision
    * its name
    * its state
    * its publication date
    * all specific attributes that are marked as public
    * all published document that are attached to this part
    * all published related revisions


The public page of a **document** shows the following data:

    * its type
    * its reference
    * its revision
    * its name
    * its state
    * its publication date
    * all specific attributes that are marked as public
    * all published part that are attached to this document
    * all published related revisions
    * its non deprecated files, for each file, the following data are available:

        * its filename
        * its size
        * its thumbnail
        * its content

The following data are **NOT** visible:

    * all user data (owner, signers, notified users, creator...)
    * all unpublished related revisions
    * all related comments
    * the history
    * the lifecycle
    * the group
    * dates of creation and last modification
    * all other data specific to a type

A published plmobject stays visible when it is deprecated.


Unpublishing a plmobject
==========================


A publication can be undone by a publisher who belongs to the object's group.

The interface should ask a confirmation and the user's password before unpublishing
a plmobject.

Browsing of published plmobject
================================

An anonymous user should be able to browse all published plmobject.
He must not be able to see an unpublished object while browsing all
objects.

