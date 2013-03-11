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

Two functions are available to render a text:

 * :func:`plmapp.filters.richtext`
 * :func:`plmapp.filters.plaintext`

The first one returns an HTML output,
the second one returns a plain text output.
The plain text output is stored and indexed by the search engine.

Both functions take the text to render and the current object
(usually a controller). The current object is required to
render relative links (like links to the next/previous revisions).

Template filters
++++++++++++++++

Two template filters are available to render a text in a template:

 * :func:`.richtext_filter`
 * :func:`.plaintext_filter`

Both filters take a text to render and the current object:

.. code-block:: django

    {% load plmapp_tags %}
    ...
    {{ text|richtext_filter:obj}} 

or

.. code-block:: django

    {% load plmapp_tags %}
    ...
    {{ text|plaintext_filter:obj}} 

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

Creation and modification forms automatically convert
textarea widget to the enhanced version as set
by the :setting:`RICHTEXT_WIDGET_ClASS` settings.

If you need to enhance a textarea, you can call 
:func:`.forms.enhance_fields` if the form was built from a model.
Alternatively, you can enhance any form like this::

    from django.conf import settings
    from openPLM.plmapp.utils.importing import import_dotted_path

    def enhance_form(form_cls, field):
        widget_class = getattr(settings, "RICHTEXT_WIDGET_CLASS", None)
        if widget_class is not None:
            cls = import_dotted_path(widget_class)
            form_cls.base_fields[field].widget = cls()
        return form_cls


Markdown syntax
==================

Python Markdown

Extensions



How to add a new syntax
=========================


.. warning::

    Safe mode
