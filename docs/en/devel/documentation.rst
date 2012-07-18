========================
Documenting OpenPLM
========================

If you want to contribute to this documentation, here are some instructions.


Tools used to write the documention
========================================

This documentation is written with `Sphinx <http://sphinx.pocoo.org/>`_.

Here are some links about this wonderful tool and the reStructuredText language:

    * http://thomas-cokelaer.info/tutorials/sphinx/rest_syntax.html
    * http://docutils.sourceforge.net/rst.html
    * http://readthedocs.org/docs/pvdevtools/en/latest/devel/documentation/sphinx/index.html

Compiling the documentation
==============================

    * ``cd docs/``
    * ``make html`` or :samp:`make LANGUAGE={lang} html`

You may also try another output format but html format is the preferred one.


Directories 
============

The documentation is available in several languages. There is one directory
per language. It duplicates some contents but it makes it possible to change screenshots
and it is simple to avoid duplicated reST references by using independant directories.

The :file:`docs` directory contains one directory per language (``en``, ``fr``...) and
a :file:`skel` directory. This last directory is intended to simply add a language
by copying it.

Each documentation directory contains the following files and directories:

.. highlight:: none

::

    admin                -> administrator documentation 
    _build               -> built files are here
    conf.py              -> Sphinx configuration file
    devel                -> developer documentation, can be a symlink to ../en/devel
    index.rst            -> documentation home page
    Makefile             
    specs                -> specifications, can be a symlink to ../en/specs
    _static              -> static files 
    _templates           -> sphinx templates, including the one to select the language
    user                 -> user documentation
    whatsnew             -> documentation describing new features
    and some .rst files


.. 
    Remember, friendship is magic.
