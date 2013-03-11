.. versionadded:: 1.3

==========================================================
Rich text | Wiki syntax
==========================================================


Introduction
================


Model: how to enhance a textfield 
===================================

Example:

.. code-block:: python
    :emphasize-lines: 4
    
    class MyModel(Part):

        my_text_field = models.TextField()
        my_text_field.richtext = True

How to render a content
===========================

Functions
++++++++++++++


Template tags
+++++++++++++++


Views, ajax
++++++++++++

One AJAX view (:func:`.ajax_richtext_preview`) is available to 
get an HTML preview of a content.

URLs:

    PLMObject
        :samp:`/ajax/richtext_preview/{type}/{reference}/{revision}/`

    User
        :samp:`/ajax/richtext_preview/User/{username}/-/`

    Group
        :samp:`/ajax/richtext_preview/Group/{name}/-/`


This view requires one GET parameter, ``content`` which is the
raw content to be rendered.

It returns a JSON response with one key, ``html``, the rendered
content that can be included in a div element.

Forms
+++++++

Markdown syntax
==================

Python Markdown

Extensions



How to add a new syntax
=========================


.. warning::

    Safe mode
