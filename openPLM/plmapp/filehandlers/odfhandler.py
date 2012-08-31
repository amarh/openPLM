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

from base import HandlersManager, FileHandler
from openPLM.plmapp.utils import size_to_format

# see odfpy (sudo easy_install odfpy)
from odf.opendocument import load
from odf.meta import DocumentStatistic
from odf.style import PageLayoutProperties
from odf.namespaces import FONS, METANS


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
            self.nb_pages = int(stat.getAttrNS(METANS, "page-count"))
            w = page.getAttrNS(FONS, 'page-width')
            h = page.getAttrNS(FONS, 'page-height')
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
