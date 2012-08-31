############################################################################
# openPLM - open source PLM
# Copyright 2010 Philippe Joulaud, Pierre Cosquer
# 
# This file is part of openPLM.
#
#    openPLM is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    openPLM is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with openPLM.  If not, see <http://www.gnu.org/licenses/>.
#
# Contact :
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pcosquer@linobject.com
################################################################################

import warnings

from base import HandlersManager, FileHandler
from openPLM.plmapp.utils import size_to_format

#  sudo apt-get install python-pypdf
warnings.simplefilter('ignore', DeprecationWarning)
from pyPdf import PdfFileReader
warnings.simplefilter('default', DeprecationWarning)

class PDFHandler(FileHandler):
    """
    This :class:`.FileHandler` can parse opendocument (``".odt"``) files.

    :attributes:
        .. attribute:: nb_pages
            
            number of pages of the file
    """

    def __init__(self, path, filename):
        super(PDFHandler, self).__init__(path, filename)
        warnings.simplefilter('ignore', DeprecationWarning)
        try:
            pdf = PdfFileReader(file(path, "rb"))
            info = pdf.getDocumentInfo()
            if info.title:
                self.title = info.title
            if info.subject:
                    self.subject = info.subject
            self.nb_pages = pdf.gtNumPages()
            # TODO : format
            page = pdf.getPage(0)
            page.mediaBox
            self._set_valid()
        except Exception, e:
            # load may raise several exceptions...
            self._set_invalid()
        warnings.simplefilter('default', DeprecationWarning)
    
    @property
    def attributes(self):
        res = []
        for attr in ("nb_pages", "title", "subject"):
            if hasattr(self, attr):
                res.append(attr)
        return res

HandlersManager.register(".pdf", PDFHandler)
