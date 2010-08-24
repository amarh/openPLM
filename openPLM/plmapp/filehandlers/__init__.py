"""
This module contains utilities to retrieve informations from a file.

Its main purpose is to be used by :meth:`.DocumentController.handle_added_file`.

For example, if you have a model called *PDFDocument* with an attribute called
*nb_pages*, you can update this attribute when a file is uploaded::

    import os

    from django.db import models

    from openPLM.plmapp.filehandlers import HandlersManager
    from openPLM.plmapp.models import Document
    from openPLM.plmapp.controllers import DocumentController
   
    # our model
    class PDFDocument(Document):
        nb_pages = models.PositiveIntegerField(default=lambda: 0)

    # its controller
    class PDFDocumentController(DocumentController):

        def handle_added_file(self, doc_file):
            # check if if it is a pdf file
            if os.path.splitext(doc_file.file.path)[1].lower() == ".pdf":
                # get an handler for a pdf files
                handler_cls = HandlersManager.get_best_handler(".pdf")
                # instanciate thi handler (it parses the file)
                handler = handler_cls(doc_file.file.path, doc_file.filename)
                if handler.is_valid():
                    # the handler has successfully parsed the file, so we can
                    # set the attribute *nb_page*
                    self.nb_pages = handler.nb_pages
                    self.save()
"""

from base import FileHandler, HandlersManager
from odfhandler import ODFHandler
from pdfhandler import PDFHandler

