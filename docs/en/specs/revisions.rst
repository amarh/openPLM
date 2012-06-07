=======================
Revisions
=======================

This document defines which elements should be suggested when a document or a part
is revised.

Suggested parts when a document is revised
===========================================


.. csv-table:: Parts bound to the document
    :header: "Part's state", "Existing superior revisions *bound* to the document?", "Existing superior revisions *unbound* to the document?", "Suggested?"
    :widths: 20, 30, 30, 20

    draft,   no, no, **yes**
    draft,   no, yes,no
    draft,   yes,no, no
    draft,   yes,yes,no
    proposed,no, no, **yes**
    proposed,no, yes,no
    proposed,yes,no, no
    proposed,yes,yes,no
    official,no, no, **yes**
    official,no, yes,no
    official,yes,no, no
    official,yes,yes,no
    deprecated,  no, no, no
    deprecated,  no, yes,no
    deprecated,  yes,no, no
    deprecated,  yes,yes,no

-----

.. csv-table:: Parts unbound to the document    
    :header: "Part's state", "Existing inferior revisions *bound* to the document?", "Existing inferior revisions *unbound* to the document?", "Suggested?" 
    :widths: 20, 30, 30, 20

    draft, no, no, no 
    draft, no, yes, no 
    draft, yes, no, **yes** 
    draft, yes, yes, **yes** 
    proposed, no, no, no 
    proposed, no, yes, no 
    proposed, yes, no, no 
    proposed, yes, yes, no 
    official, no, no, no 
    official, no, yes, no 
    official, yes, no, no 
    official, yes, yes, no 
    deprecated, no, no, no 
    deprecated, no, yes, no 
    deprecated, yes, no, no 
    deprecated, yes, yes, no 
                        
Suggested documents when a part is revised
============================================

.. csv-table:: Documents bound to the part   
    :header: "Document's state", "Existing superior revisions *bound* to the part?", "Existing superior revisions *unbound* to the part?", "Suggested?"
    :widths: 20, 30, 30, 20

    draft, no, no, **yes**
    draft, no, yes, **yes**
    draft, yes, no, no
    draft, yes, yes, no
    proposed, no, no, no
    proposed, no, yes, no
    proposed, yes, no, no
    proposed, yes, yes, no
    official, no, no, **yes**
    official, no, yes, **yes**
    official, yes, no, **yes**
    official, yes, yes, no
    deprecated, no, no, no
    deprecated, no, yes, no
    deprecated, yes, no, no
    deprecated, yes, yes, no

-----

.. csv-table:: Documents unbound to the part   
    :header: "Document's state", "Existing inferior revisions *bound* to the part?", "Existing inferior revisions *unbound* to the part?", "Suggested?"
    :widths: 20, 30, 30, 20

    draft, no, no, no
    draft, no, yes, no
    draft, yes, no, **yes**
    draft, yes, yes, **yes**
    proposed, no, no, no
    proposed, no, yes, no
    proposed, yes, no, no
    proposed, yes, yes, no
    official, no, no, no
    official, no, yes, no
    official, yes, no, **yes**
    official, yes, yes, **yes**
    deprecated, no, no, no
    deprecated, no, yes, no
    deprecated, yes, no, no
    deprecated, yes, yes, no

Children suggested when a part is revised
==========================================

openPLM must suggest to copy the current BOM.

Parents suggested when a part is revised
============================================================

If a parent is selected, its BOM is updated so that it does not contain
the old and the new revisions.

.. csv-table:: Parents bound to the part   
    :header: "Parent's state", "Existing superior revisions *bound* to the part?", "Existing superior revisions *unbound* to the part?", "Suggested?"
    :widths: 20, 30, 30, 20

    draft, no, no, **yes**
    draft, no, yes, **yes**
    draft, yes, no, no
    draft, yes, yes, no
    proposed, no, no, **yes**
    proposed, no, yes, no
    proposed, yes, no, no
    proposed, yes, yes, no
    official, no, no, **yes**
    official, no, yes, **yes**
    official, yes, no, no
    official, yes, yes, no
    deprecated, no, no, no
    deprecated, no, yes, no
    deprecated, yes, no, no
    deprecated, yes, yes, no

-----

.. csv-table:: Parents unbound to the part
    :header: "Parent's state", "Existing inferior revisions *bound* to the part?", "Existing inferior revisions *unbound* to the part?", "Suggested?"
    :widths: 20, 30, 30, 20

    draft, no, no, no
    draft, no, yes, no
    draft, yes, no, **yes**
    draft, yes, yes, **yes**
    proposed, no, no, no
    proposed, no, yes, no
    proposed, yes, no, no
    proposed, yes, yes, no
    official, no, no, no
    official, no, yes, no
    official, yes, no, **yes**
    official, yes, yes, **yes**
    deprecated, no, no, no
    deprecated, no, yes, no
    deprecated, yes, no, no
    deprecated, yes, yes, no
       
If a part which is not a parent is selected, data (quantity, order, unit) from
the most recent bound revision are copied.

