============================
  Bill of materials -- BOM
============================

Definition
==========

In openPLM, all parts have a bill of materials (BOM) which lists the children parts that
compose a part.
A BOM lists for each child part how much is needed to build or assembly
the parent part.

openPLM manages single-line BOM (first level of children) and indented BOM
(all levels of children).

How the BOM is stored
======================

openPLM stores each row of a BOM but it only stores the first level.
Indented BOM are dynamically built.

For example, the following (simplified) BOM is stored with 3 rows.

===== ======= ========
Level Element Quantity  
===== ======= ========
 ---   P0       ---
  1    P1        2   
  2    P2        4
  1    P2        5
===== ======= ========

The rows are (notation: parent, child, quantity):

    * P0, P1, 2
    * P1, P2, 4
    * P0, P2, 5

The model behind these rows is :class:`.ParentChildLink`. It has the following
fields:

    parent
        id of a part

    child
        id of a part

    quantity
        amount of child

    unit
        unit of the quantity (like kg, m)

    order
        field to order (sort) the BOM

    ctime
        date of creation of the row

    end_time
        date of deletion of the row (null value means no deletion)

The *ctime* and *end_time* fields allow openPLM to track changes of a BOM.
For example, if the quantity changes, the row is not deleted but, its *end_time*
field is set and a new row is created.

For example, the following BOM (date of creation: 2012/01/01) is

===== ======= ======== ==== =====
Level Element Quantity Unit Order
===== ======= ======== ==== =====
 ---   P0       ---     --   ---
  1    P1        2      m    100 
===== ======= ======== ==== =====

is stored as one row: parent -> P0, child -> P1, quantity -> 2, unit -> m,
order -> 100, ctime -> 2012/01/01, end_time -> null.

If an user changes the unit to km and the quantity to 3,
the BOM will be

===== ======= ======== ==== =====
Level Element Quantity Unit Order
===== ======= ======== ==== =====
 ---   P0       ---     --   ---
  1    P1        3      km   100 
===== ======= ======== ==== =====

and the database will contains two rows (date of modification: 2012/01/02):

    * parent -> P0, child -> P1, quantity -> 2, unit -> m,
      order -> 100, ctime -> 2012/01/01, end_time -> 2012/01/02

    * parent -> P0, child -> P1, quantity -> 3, unit -> km,
      order -> 100, ctime -> 2012/01/02, end_time -> null

If he adds a new child (P2, date of addition: 2012/01/03):

===== ======= ======== ==== =====
Level Element Quantity Unit Order
===== ======= ======== ==== =====
 ---   P0       ---     --   ---
  1    P1        2      km   100 
  1    P2       120      m   200 
===== ======= ======== ==== =====

The database will contains 3 rows:

    * parent -> P0, child -> P1, quantity -> 2, unit -> m,
      order -> 100, ctime -> 2012/01/01, end_time -> 2012/01/02

    * parent -> P0, child -> P1, quantity -> 3, unit -> km,
      order -> 100, ctime -> 2012/01/02, end_time -> null

    * parent -> P0, child -> P3, quantity -> 120, unit -> m,
      order -> 200, ctime -> 2012/01/03, end_time -> null

So previous rows are not altered since they have not been modified.

.. _bom_extensions:

Extensions
==========

Purpose
--------

Some applications need to store additional data on each row. These data
should or should not be displayed or editable. For example, an electronic CAD
application adds a *referenced designator* field which tells where a component
is put on a board. This field must be displayed and is editable. Another
application can add several location fields per row which tell where each
child element is located. These location field would be invisible but are
useful to generate a STEP document from the BOM.

Implementation
--------------

openPLM has a model named :class:`.ParentChildLinkExtension` to store these
extensions. An application can add a model that extends
:class:`.ParentChildLinkExtension` and register it. The application only has
to override some methods and openPLM will handle the display and edition of
the BOM. 

.. admonition:: PCLE and pcle

    Starting from here, PCLE means a model that extends a
    ParentChildLinkExtension and pcle means an instance of a
    ParentChildLinkExtension

A PCLE has one mandatory field, *link* which is a foreign key to a
:class:`.ParentChildLink`.

When a :class:`.ParentChildLink` is duplicated (after a modification from an
user), its bound extensions are duplicated by calling their
:meth:`.ParentChildLinkExtension.clone` method.

Registration
------------

By default, a PCLE will not be used by openPLM and must be registered.
A PCLE can be registered by calling the :func:`.registered_pcle` function.

By default, a registered PCLE applies to all BOM. It is possible to change
this behaviour by overriding the method
:meth:`.ParentChildLinkExtension.apply_to`. This method takes one argument,
the parent which will have a child, so it is possible to test its type or some
of its attributes.

Visible and invisible fields
----------------------------

A PCLE can have as many fields as needed. Added fields are hidden by default.
The classmethod :meth:`.ParentChildLinkExtension.get_visible_fields` can be
overridden to return a list of visible fields.

The classmethod :meth:`.ParentChildLinkExtension.get_editable_fields` is
called to get the list of editable fields that are added to the "add child"
form and to the "edit bom" form. By default, it returns the list of visible
fields.

.. warning::

    If a PCLE has at least one visible field, openPLM can create at most one 
    pcle per link and it will not be able to display several columns for the
    same field.    

    This behaviour is intended to keep the BOM readable and easily
    editable. 

    If you really need several visible pcles per link, you can create
    your own models.Field and play with its :meth:`formfield` method.
    
Cloning
--------

:class:`.ParentChildLink` are never deleted but they are cloned. And since
a pcle is bound to a link, it must be clonable. A PCLE must define
the :meth:`.ParentChildLinkExtension.clone` method. By default, it raises
a :exc:`NotImplementedError` exception.


Examples
--------

Reference designator field
**************************

.. code-block:: python
        
    class ReferenceDesignator(ParentChildLinkExtension):
        
        reference_designator = models.CharField(max_length=200, blank=True)

        def __unicode__(self):
            return u"ReferenceDesignator<%s>" % self.reference_designator

        @classmethod
        def get_visible_fields(cls):
            return ("reference_designator", )

        @classmethod
        def apply_to(cls, parent):
            # only apply to mother boards
            return isinstance(parent, MotherBoard)
       
        def clone(self, link, save, **data):
            ref = data.get("reference_designator", self.reference_designator)
            clone = ReferenceDesignator(link=link, reference_designator=ref)
            if save:
                clone.save()
            return clone

    register(ReferenceDesignator)
    register_PCLE(ReferenceDesignator)


Hidden location fields
**********************

Since all fields are hidden, no Location objects will be by openPLM created.
A custom controller can create them but it would not have to handle their cloning. 

.. code-block:: python

    class Location(ParentChildLinkExtension):
        
        x = models.FloatField(default=lambda: 1)
        y = models.FloatField(default=lambda: 1)
        z = models.FloatField(default=lambda: 1)

        def __unicode__(self):
            return u"<Location<%f, %f, %f>" % (self.x, self.y, self.z)

        @classmethod
        def apply_to(cls, parent):
            # only apply to all parts
            return True
       
        def clone(self, link, save, **data):
            x = data.get("x", self.x)
            y = data.get("y", self.y)
            z = data.get("z", self.z)
            clone = Location(link=link, x=x, y=y, z=z)
            if save:
                clone.save()
            return clone

    register(Location)
    register_PCLE(Location)

.. _bom_comparison:

.. versionadded:: 1.2

BOMs comparison
================

Since the version 1.2, it's possible to compare two BOMs at two different dates
and renders a diff view showing differences side by side (like in trac).

The method :meth:`.PartController.cmp_bom` performs the comparison and the view
:func:`.compare_bom` renders the result.

This comparison relies :meth:`.difflib.SequenceMatcher.get_opcodes`.
The standard :mod:`.difflib` module can compare strings and any types of finite
sequences. Using this module is only a matter of input formats. In OpenPLM, BOMs
are flatten (see :func:`.flatten_bom`) and three lines of code do the comparison.





