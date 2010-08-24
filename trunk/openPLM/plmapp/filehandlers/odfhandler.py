from base import HandlersManager, FileHandler
from openPLM.plmapp.utils import size_to_format

# see odfpy (sudo easy_install odfpy)
from odf.opendocument import load
from odf.meta import DocumentStatistic
from odf.style import PageLayoutProperties


class ODFHandler(FileHandler):
    """
    This :class:`.FileHandler` can parse opendocument (``".odt"``) files.

    :attributes:
        .. attribute:: nb_pages
            
            number of pages of the file
        .. attribute:: format

            format of the file (``"A0"`` to ``"A4"`` or ``"Other"``)
    """

    def __init__(self, path, filename):
        super(ODFHandler, self).__init__(path, filename)
        try:
            doc = load(path)
            stat = doc.getElementsByType(DocumentStatistic)[0]
            page = doc.getElementsByType(PageLayoutProperties)[0]
            self.nb_pages = int(stat.attributes["meta:page-count"])
            w = page.attributes['fo:page-width']
            h = page.attributes['fo:page-height']
            self.format = size_to_format(w, h)
            self._set_valid()
        except Exception, e:
            # load may raise several exceptions...
            self._set_invalid()
    
    @property
    def attributes(self):
        res = []
        for attr in ("nb_pages", "format"):
            if hasattr(self, attr):
                res.append(attr)
        return res

HandlersManager.register(".odt", ODFHandler)
