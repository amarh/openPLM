.. _rest-account-specs:

=========================
 Restricted access
=========================

.. versionadded:: 1.1


This document describes which contents can be accessed by an user
who has restricted access rights.


Restricted Account
===================

A restricted account has the ``restricted`` field of its profile set to
True.

A restricted account can neither be a contributor nor an administrator.

A restricted account can not be in a group.


Accessible parts and documents
================================

Published parts and documents are accessible.

Public pages of parts and documents which reading access has been given by
their owner are accessible.

All members of the object's group can give access to an object if its state
is official.

All members of the object's group can remove access to an object whatever 
its state.


Inaccessible contents
=====================

    * API
    * Search results
    * Navigate
    * Groups
    * User pages
    * Object pages excepted public pages
    * Create pages (create, import, sponsor)
    * Comments
    * Ajax views


Accessible contents
====================

    * Public pages
    * Public download
    * User's attributes page of the logged user (without comments)
    * Parts-DOC-CAD page of the logged user
    * Change password page
    * Browse: only accessible parts and documents
    * Home page: only the browse and study buttons are enabled.
    * Thumbnails (an administrator may deny this access)  

Contents that are not in this list are inaccessible.

Rights delegation
===================

A restricted account can not delegate its rights.

An user (restricted or not) can not delegate its rights to a restricted account.


