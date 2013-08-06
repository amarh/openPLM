.. _user-richtext:

===================================================
Wiki (Markdown) syntax
===================================================

.. highlight:: text

Introduction
===============

http://daringfireball.net/projects/markdown/syntax


Headers
==========================

::

    # Main title (H1) #

    ## Second level (H2) ##

    ### Third level (H3) ###


or

::


    # Main title (H1) 

    ## Second level (H2) 

    ### Third level (H3)

or

::

    Main title
    ===========

    Subtitle
    -----------


Table of contents
++++++++++++++++++++

::
    
    [TOC]

renders a table of contents.


Lists
========

Ordered lists
++++++++++++++++

::

     1. item 1
     2. item 2
     3. item 3

renders as:

.. container:: syntax-example

    1. item 1
    2. item 2
    3. item 3


Sub items must be indented with 4 spaces:

::

     1. item 1
        1. sub item 1
        2. sub item 2
     2. item 2
     3. item 3

renders as:

.. container:: syntax-example

    1. item 1
        1. sub item 1
        2. sub item 2
    2. item 2
    3. item 3

Unordered lists
+++++++++++++++++++

::
    
    + Pinkie pie
    + Twilight Sparkle
    + Rainbow Dash

and::

    - Pinkie pie
    - Twilight Sparkle
    - Rainbow Dash

and::

    * Pinkie pie
    * Twilight Sparkle
    * Rainbow Dash

render as:

.. container:: syntax-example

    * Pinkie pie
    * Twilight Sparkle
    * Rainbow Dash



Quotes
=================

::

    Quote:

    > A quote starts with a >
    > This sentence is in the first paragraph
    >
    > Paragraphs are separated by a new line 

renders as:

.. container:: syntax-example

    Quote:

        A quote starts with a >
        This sentence is in the first paragraph
        
        Paragraphs are separated by a new line 

    
Hyperlinks
======================


::
    
    A link to <http://example.com>

renders as:

.. container:: syntax-example

    A link to `<http://example.com>`_


::

    This is [an example](http://example.com/) inline link.

renders as:

.. container:: syntax-example

    This is `an example <http://example.com/>`_ inline link.


Additions to the Markdown syntax:


.. list-table::

    * - :samp:`[{type}/{reference}/{revision}]`
      - link to a part or document
    * - :samp:`part:"{name}"` or :samp:`part:{name}`
      - link to the most recent part named *name*
    * - :samp:`doc:"{name}"` or :samp:`doc:{name}`
      - link to the most recent document named *name*
    * - :samp:`<<`
      - link to the previous revision of the current object
    * - :samp:`>>`
      - link to the next revision of the current object
    * - :samp:`@{username}`
      - link to a user page
    * - :samp:`group:{name}`
      - link to a group


Inline markup
=============

========================== ======================
``*emphasize*``            *emphasize*
``_emphasize_``            *emphasize*
``**emphasize strongly**`` **emphasize strongly**
``__emphasize strongly__`` **emphasize strongly**
```code```                 ``code``
========================== ======================



Images
==========

::

    ![Alt text](http://example.com/img.jpg)

Tables
=========

::

    First Header  | Second Header
    ------------- | -------------
    Content Cell  | Content Cell
    Content Cell  | Content Cell

renders as:

.. container:: syntax-example
    
    =============  =============
    First Header   Second Header
    =============  =============
    Content Cell   Content Cell
    Content Cell   Content Cell
    =============  =============



Code
======



::

    *code*:

        Code examples must be indented with 4 spaces

          **not strong**

           
         indentations
         and line breaks are preserved

renders as:

.. container:: syntax-example

    *code*::

        Code examples must be indented with 4 spaces

          **not strong**

           
         indentations
         and line breaks are preserved

