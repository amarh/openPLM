#! /usr/bin/env python
#-!- coding:utf-8 -!-

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
#    Pierre Cosquer : pcosquer@linobject.com
################################################################################

"""
This script checks that all dependencies are installed.
"""

installed = []
not_installed = []

import sys
if sys.version_info < (2, 6):
    print "The version of Python is too old (2.6 required, found %s" % sys.version
    not_installed.append("python")

try:
    import django
    if django.VERSION >= (1, 5):
        installed.append("django")
    else:
        print "the version of django is too old (1.5 required, found %s)" % django.get_version()
        not_installed.append("django")
except ImportError:
    print "django is not installed, see http://djangoproject.com"
    not_installed.append("django")

try:
    import pygraphviz
    if tuple(pygraphviz.__version__.split(".")) >= (1, 1):
        installed.append("django")
    else:
        print "the version of pygraphviz is too old (1.1 required, found %s)" % pygraphviz.__version__
        not_installed.append("pygraphviz")
except ImportError:
    print "pygraphviz is not installed, see http://networkx.lanl.gov/pygraphviz/"
    not_installed.append("pygraphviz")

try:
    import kjbuckets
    installed.append("kjbuckets")
except ImportError:
    print "kjbuckets is not installed, see http://gadfly.sourceforge.net/kjbuckets.html"
    not_installed.append("kjbuckets")

try:
    import odf
    installed.append("odf")
except ImportError:
    print "odfpy is not installed, see http://odfpy.forge.osor.eu/"
    not_installed.append("odf")

try:
    import pyPdf
    installed.append("pyPdf")
except ImportError:
    print "pyPdf is not installed, see http://pybrary.net/pyPdf/"
    not_installed.append("pyPdf")

try:
    import Image
    installed.append("Image")
except ImportError:
    print "PIL is not installed, see http://www.pythonware.com/products/pil/"
    not_installed.append("PIL")

if not_installed:
    print "Error: %s are not installed" % (", ".join(not_installed))
else:
    print "All is ok"

