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
#    along with Foobar.  If not, see <http://www.gnu.org/licenses/>.
#
# Ce fichier fait parti d' openPLM.
#
#    Ce programme est un logiciel libre ; vous pouvez le redistribuer ou le
#    modifier suivant les termes de la “GNU General Public License” telle que
#    publiée par la Free Software Foundation : soit la version 3 de cette
#    licence, soit (à votre gré) toute version ultérieure.
#
#    Ce programme est distribué dans l’espoir qu’il vous sera utile, mais SANS
#    AUCUNE GARANTIE : sans même la garantie implicite de COMMERCIALISABILITÉ
#    ni d’ADÉQUATION À UN OBJECTIF PARTICULIER. Consultez la Licence Générale
#    Publique GNU pour plus de détails.
#
#    Vous devriez avoir reçu une copie de la Licence Générale Publique GNU avec
#    ce programme ; si ce n’est pas le cas, consultez :
#    <http://www.gnu.org/licenses/>.
#    
# Contact :
#    Philippe Joulaud : ninoo.fr@gmail.com
#    Pierre Cosquer : pierre.cosquer@insa-rennes.fr
################################################################################

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
