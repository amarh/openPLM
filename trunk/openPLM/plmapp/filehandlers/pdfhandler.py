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
