.. _devel-richtext:

==========================================================
Rich text | Wiki syntax
==========================================================

.. versionadded:: 2.0


Introduction
================

OpenPLM 2.0 introduces a wiki syntax to comments and some text fields.

The code and this documentation speak about rich text instead of a
wiki content as it is not really a wiki engine (no WikiLink automatically
created).

This document describes how to mark a text field as a rich text field
and how to render its content.



Model: how to enhance a textfield 
===================================

OpenPLM does not store the rendered HTML. So it is possible to set
a text field as a "rich" text field at any time. To do that,
simply add a ``richtext`` attribute (set tot True) to the text field.

Example:

.. code-block:: python
    :emphasize-lines: 4
    
    class MyModel(Part):

        my_text_field = models.TextField()
        my_text_field.richtext = True

Note that a plain text rendering is stored by the search engine.
This plain text rendering is syntax dependant and you may have 
to reindex a model if the raw text (user input stored in the database)
and the plain text may be too different.

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

OpenPLM ships with a `Markdown`_ syntax.

It can be enabled with the following settings::

    RICHTEXT_FILTER = 'openPLM.plmapp.filters.markdown_filter'
    RICHTEXT_WIDGET_CLASS = 'openPLM.plmapp.widgets.MarkdownWidget'

The filter is built with `Python Markdown`_ with the ``safe_mode`` option activated
and the following extensions:

    * ``abbr``,
    * ``tables``,
    * ``def_list``,
    * ``smart_strong``, 
    * ``toc``.

More custom extensions are enabled, they added the following syntaxes:

.. list-table::

    * - :samp:`[{type}/{reference}/{revision}]`
      - link to a PLMObject
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


The javascript editor is based on `MarkEdit`_, it renders the preview
with :func:`.ajax_richtext_preview`.

.. _Python Markdown: http://pythonhosted.org/Markdown/index.html

.. _Markdown: http://daringfireball.net/projects/markdown/

.. _MarkEdit: http://tstone.github.com/jquery-markedit/


How to add a new syntax
=========================

.. warning::

    Be careful, markup libraries may have features that allow raw HTML to be
    included, and that allow arbitrary files to be included. These can lead to
    XSS vulnerabilities and leaking of private information. It is your
    responsibility to check the features of the library you are using and
    configure it appropriately to avoid this.


To add a new syntax, you only have to write one function that
will convert the content.
This function is registered by the :setting:`RICHTEXT_FILTER` setting
which must be the complete python path to the function
(``application.module.function_name``).
OpenPLM will automatically import the module and call the function instead
of the default implementation.


The function must take two arguments:

    * the content to convert
    * the current object

It must return a unicode string which should mark as safe if it
is a safe html content.

Example::

    # apps/my_filter/filters.py
    from django.utils.safestring import mark_safe

    def my_filter(content, obj):
        # do something with content
        html = f(content)
        return mark_safe(html)

::

    # settings.py
    RICHTEXT_FILTER = 'openPLM.apps.my_filter.filters.my_filter'

.. note::

    Be careful with all security issues. Moreover, this function
    should never fail and be tolerant to syntax errors.
    Be also careful with extra features which may leak
    confidential data.


Then you can define two additional settings:

   * :setting:`RICHTEXT_PLAIN_FILTER` which should be a
     path to function.
     This function is similar to the previous filter except it
     must return a plain text without any HTML tags (content
     is escaped by openPLM).
     The default implementation cleans up the HTML code.

   * :setting:`RICHTEXT_WIDGET_CLASS` which should be a
     path to a widget class.


For example, the markdown widget is defined like this::

    from django import forms

    class MarkdownWidget(forms.Textarea):
        class Media:
            css = {
                'all': ('css/jquery.markedit.css',)
            }
            js = ('js/showdown.js', 'js/jquery.markedit.js', )

        def __init__(self):
            super(MarkdownWidget, self).__init__()
            self.attrs["class"] = "markedit"

As you can see, it defines extra css and js files.
It also sets the class attribute of the textarea so that
the javascript can easily treat the textarea
(here, ``$(".markedit").markedit()``).


