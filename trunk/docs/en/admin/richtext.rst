.. _richtext-admin:

==================================
Rich text | wiki syntax
==================================

.. versionadded:: 2.0


OpenPLM 2.0 introduces a rich syntax (wiki). It can be enabled
at any time by editing the :file:`settings.py` file.
This syntax is used to render comments, long description fields
and by the :ref:`richpage application <richpage-admin>`.

It is possible to switch to another syntax at any time but
keep in mind that old contents will be rendered with the new syntax
and may look wrong.

Available syntaxes
===================

.. note::
    All syntaxes are meant to be safe. HTML contents are escaped
    and no errors are raised in case of an invalid input.

None::
    
    RICHTEXT_FILTER = None
    RICHTEXT_WIDGET_CLASS = None

Markdown::

    RICHTEXT_FILTER = 'openPLM.plmapp.filters.markdown_filter'
    RICHTEXT_WIDGET_CLASS = 'openPLM.plmapp.widgets.MarkdownWidget'

