============================
Lifecycle
============================

.. warning::

    The following rules may not have been implemented.


Standard lifecycles
=====================

    #. All standard lifecycles shall have an official status
    #. All standard lifecycles shall have a deprecated status
    #. All standard lifecycles shall have one or more status
       before official status (draft, to be validated, ...)
    #. Only one object with the same type/reference shall be at
       official status

Promote rules for Standard lifecycles
+++++++++++++++++++++++++++++++++++++++

Parts
-------

    #. Part without children shall have at least one linked official
       document before being promoted

Documents
----------

    #. Document shall not be promoted without a file in
       it or equivalent
    #. Document shall not be promoted if one of their files is locked
        
Promote rules to official for Standard lifecycles
++++++++++++++++++++++++++++++++++++++++++++++++++++

    #. Promoting one object to official status shall
       push the prior official revision to deprecated status
    #. Promoting one object to official status shall
       push all prior non official revisions to cancel lifecycle
    #. Parent part shall not be promoted to a status
       higher than its child's status
       
Ownership
++++++++++

    #. When an object is official, ownership shall switch from
       one user to Company
    #. When an object is deprecated, ownership shall stay to Company
    #. Non official objects can't switch to Company ownership

Visibility
+++++++++++++

    #. Object is visible only by its group's users when its status is before
       official
    #. Object is visible by all users when its status is official
    #. Object is visible by all users when its status is deprecated

Edit/Modification
++++++++++++++++++

    #. Object can only be edited by its owner
    #. Part links can be created/removed only by its owner
    #. Part links can't be removed at official status
    #. Part's child links can't be created/removed at official status
    #. Part's parent links can be created/removed at official status
    #. Documents links can be created/removed at all status
    #. Ownership and other signature rights can be modified only by its owner

Revision
++++++++++

    #. All users who can see an object can revise it
    #. Only the last revision can be revised
    #. An object can be revised whatever is its status (except deprecated)

Notification
+++++++++++++

    #. When an object is promoted to official status,
       all members of the group shall be notified by e-mail
    #. When an object is promoted the next signer shall be notified by e-mail
    #. When an object is demoted the previous signer shall be notified by
       e-mail


Cancel lifecycle
====================

(not yet implemented)

    #. Shall have only one status: Cancel
    #. Object is visible by all users
    #. Ownership is Company
    #. Object is cancel if it is pushed by another promoted to
       official status
    #. All part-part and part-document links shall be removed
    #. Cancelled objects can't be edited nor modified
    #. Users can't revise an object with cancel status

