.. _publication-devel:

==============
Publication
==============

.. versionadded:: 1.1

This document describes how the :doc:`Publication specification </specs/publication>`
is implemented.

Publishers
==========

A new boolean field :attr:`.UserProfile.can_publish` is added to each :class:`.UserProfile`.
By default, this field is set to ``False``.
If this field is set to ``True``, the user can publish an object (if all
other rules are respected).

The migration :file:`plmapp/migrations/0014_auto__add_field_userprofile_can_publish.py`
adds this field (set to False) to all existing users.

This field is neither a creation field nor a modification field.
Only an admin can modify this field via the admin interface.

Model
======

PLMObject
++++++++++

A new boolean field :attr:`.PLMObject.published` is added to each :class:`.PLMObject`.
By default, this field is set to ``False``.
If this field is set to ``True``, it means the object has been published
and is accessible to anonymous users.

The migration :file:`plmapp/migrations/0015_auto__add_field_plmobject_published.py`
adds this field (set to False) to all existing plmobjects.


A new property named :attr:`.PLMObject.published_attributes` returns the
list of published attributes.
By default, it returns the following attributes:

    1. type
    #. reference
    #. revision
    #. name

This property can be overriden by a custom model to add more attributes.

History
+++++++

All publication and unpublication are stored in the :class:`.History` table.

A publication is stored with the :attr:`.AbstractHistory.action` field
set to ``Publish``.

A unpublication is stored with the :attr:`.AbstractHistory.action` field
set to ``Unpublish``.


Controller
==========

Publishing a document
++++++++++++++++++++++

Methods
--------

The following methods are available to publish a PLMObject and test
if a PLMObject can be published:

    * :meth:`.PLMObjectController.publish`

    * :meth:`.PLMObjectController.check_publish`

    * :meth:`.PLMObjectController.can_publish`

Tests
-----

    * :meth:`.ControllerTest.test_publish_not_official`

    * :meth:`.ControllerTest.test_publish_official`

    * :meth:`.ControllerTest.test_publish_deprecated`

    * :meth:`.ControllerTest.test_publish_published`

    * :meth:`.ControllerTest.test_publish_not_publisher`

    * :meth:`.ControllerTest.test_publish_not_in_group`


Unpublishing a document
+++++++++++++++++++++++

Methods
--------

The following methods are available to unpublish a PLMObject and test
if a PLMObject can be unpublished:

    * :meth:`.PLMObjectController.unpublish`

    * :meth:`.PLMObjectController.check_unpublish`

    * :meth:`.PLMObjectController.can_unpublish`

Tests
-----

    * :meth:`.ControllerTest.test_unpublish_not_official`

    * :meth:`.ControllerTest.test_unpublish_official`

    * :meth:`.ControllerTest.test_unpublish_deprecated`

    * :meth:`.ControllerTest.test_unpublish_published`

    * :meth:`.ControllerTest.test_unpublish_not_publisher`

    * :meth:`.ControllerTest.test_unpublish_not_in_group`


Views
=====

Lifecycle
++++++++++

:func:`.display_object_lifecycle` handles the publication
and unpublication of a PLMObject.

Tests
------

    * :meth:`.ViewTest.test_publish_post`

    * :meth:`.ViewTest.test_publish_post_error_not_official`
   
    * :meth:`.ViewTest.test_publish_post_error_published`
    
    * :meth:`.ViewTest.test_unpublish_post`
    
    * :meth:`.ViewTest.test_unpublish_post_error_unpublished`
   


Public
++++++

:func:`.public` view renders a published PLMObject. If the given 
object is not published, it redirects to the login page.
If the given object is neither a part nor a document, it raises
an :exc:`.Http404` exception.


Tests
------

    * :meth:`.ViewTest.test_public_get`

    * :meth:`.ViewTest.test_public_error`


Public download
+++++++++++++++

:func:`.public_download` handles the download of a published file.


Browse
++++++

:func:`.browse` allows an anonymous user to browse all published
parts and documents.

Templates
===========

lifecycle.html
+++++++++++++++

If an object has been published, this template displays a link to its
publish page.

If the user can publish the object, it adds a form named ``form-publish`` that
prompts the user password and warns the user that a published object is
accessible to anonymous user.

If the user can unpublish the object, it adds a form named ``form-unpublish`` that
prompts the user password and warns the user that a unpublished object is
no more accessible to anonymous user.


public.html
+++++++++++

If the object has been published, this template displays:

    * all non deprecated files
    * all published attributes
    * the state of the object
    * all published revisions
    * all published attached parts and documents

browse.html
+++++++++++++

If the user is not authenticated, it hides all unaccessible objects
(users, groups, unpublished object).



