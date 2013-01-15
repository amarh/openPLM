==============
Glossary
==============

.. note::
    Most of the following definitions use the term :term:`plmobject`
    to refer to a part or a document.

.. glossary::

    assembly
        a subset of components. We define an assembly creating some link(s) between one :term:`part` (parent) and one or more :term:`part` (s) (children).
        
    BOM
        Bill Of Material is a list of all :term:`part` s, including quantities, necessary to assemble/manufacture a product.
        
    cancel
        specific :term:`state` a :term:`user` utilizes to cancel a plmobject (note we can't delete anything in OpenPLM).
        
    clone
        duplicate a :term:`plmobject` (copy all its content) without creating a link between the original and the new :term:`plmobject` s 
        
    company (:term:`user`)
        company (can be changed to another name during initialisation phase) is a special and unique :term:`user`. He is the creator of the first :term:`group` and he sponsors the first :term:`user` s. He also owns all official :term:`plmobject` s.
        
    decompose
        all terms related to decompose refer to the fact of spliting a :term:`part` in multiples sub- :term:`assembly` (or subset) or :term:`part` s 
        
    demote
        demote a :term:`plmobject` means to move backward from one :term:`state` to another in its :term:`lifecycle` 
        
    document
        a container for files or similar contents (like an online resource). Creating links between :term:`document` s and :term:`part` s helps us specifying a product or a sub- :term:`assembly` (or subset) of product. 
        
    group
        a :term:`group` of :term:`user` s and :term:`plmobject` s. Some specific rights on :term:`plmobject` s who belong to a :term:`group` are allocated to :term:`user` s who belong to the same :term:`group`. May be the term :term:`group` is not the best one and we could use the term workspace or project.
        
    lifecycle
        a sequence of :term:`state` (or status) a :term:`plmobject` can take 
        
    officialize
        promote a :term:`plmobject` to its official :term:`state` 
        
    owner
        a :term:`user` who have all rights on a :term:`plmobject`
        
    part
        a real life product or service or a subset of them in OpenPLM. Creating links between parts helps us defining :term:`assembly` s sub- :term:`assembly` s and, hence, a full product structure (and :term:`BOM`). 
        
    PLM
        Product Lifecycle Management is professional application which manage product development activities. It helps people collaborating on the same product development and it ensures a tracability of the product definition (from its early stage of development to its end of life).
        
    plmobject
        (developer term) a :term:`part` or a :term:`document` 
        
    promote
        promote a :term:`plmobject` means to move forward from one :term:`state` to another in its :term:`lifecycle` 
        
    publish
        make a :term:`plmobject` accessible to anonymous :term:`user` s 
        
    publisher
        a :term:`user` who has the right to publish a :term:`plmobject` 
        
    signer
        a :term:`user` who can promote or demote a :term:`plmobject`
        
    state
        state of a :term:`plmobject` (can be draft, official, cancel, ...)
        
    user
        a real life person registered in OpenPLM
        
    unpublish
        remove anonymous access of a :term:`plmobject`
        
        
