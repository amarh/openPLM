===============================================
pdfgen -- PDF generation
===============================================

This application adds the following features:

    * export of the "attributes" page as PDF
    * export of the BOM page as PDF
    * merge of several PDF into a single one.

Dependencies
==============

This application depends on `xhtml2pdf <http://www.xhtml2pdf.com/>`_ and
`pyPDF <http://pybrary.net/pyPdf/>`_. 


settings.py
==============

To enable the *pdfgen* application, it must be enabled in the settings file: add
``'openPLM.apps.pdfgen'`` to the list of installed applications
(:const:`INSTALLED_APPS`).

Testing
=========

To test this application, create a part. Then visited its "attributes" page
and click on the "Download as PDF" button. If all is ok, you should download
a PDF similar to the "attributes" page


