import warnings

_msg = """The 'openPLM.plmapp.fileformats' module has moved to 'openPLM.plmapp.files.formats'.
This module will be removed in OpenPLM 1.4."""
warnings.warn(_msg, DeprecationWarning)

from openPLM.plmapp.files.formats import *
