#! /usr/bin/env python

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
    if django.VERSION >= (1, 1):
        installed.append("django")
    else:
        print "the version of django is too old (1.1 required, found %s)" % django.get_version()
        not_installed.append("django")
except ImportError:
    print "django is not installed, see http://djangoproject.com"
    not_installed.append("django")

try:
    import pygraphviz
    if pygraphviz.__version__ >= "0.99.1":
        installed.append("django")
    else:
        print "the version of pygraphviz is too old (0.99.1 required, found %s)" % pygraphviz.__version__
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
    import pyPdf
    installed.append("Image")
except ImportError:
    print "PIL is not installed, see http://www.pythonware.com/products/pil/"
    not_installed.append("PIL")

if not_installed:
    print "Error: %s are not installed" % (", ".join(not_installed))
else:
    print "All is ok"

