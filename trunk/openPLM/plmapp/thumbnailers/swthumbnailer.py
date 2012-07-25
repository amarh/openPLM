"""
This module adds a thumbnailer for SolidWorks file.

How it works
============

A SolidWorks file is an `OLE`_ file. This file contains
an entry named ``PreviewPNG`` (or :samp:`{Something-}PreviewPNG`)
which contains the thumbnail as a PNG file.

This thumbnailer uses :command:`gsf` (from ``libgsf-bin``) to find the name
of the entry and to extract its content.

.. _OLE: http://en.wikipedia.org/wiki/Object_Linking_and_Embedding

"""

import re
import subprocess

from base import ThumbnailersManager

def sw_thumbnailer(input_path, original_filename, output_path):
    """
    Thumbnailer that extracts a thumlbnail of a SolidWorks file.
    """
    out = subprocess.Popen(["gsf", "list", input_path], stdout=subprocess.PIPE).communicate()[0]
    previews = re.findall("[\w/-]*PreviewPNG", out)
    if not previews:
        raise ValueError("No preview found")
    done = False
    for preview in previews:
        with open(output_path, "wb") as png_file:
            args = ["gsf", "cat", input_path, preview]
            call = subprocess.call(args, stdout=png_file)
            done = call == 0
        if done:
            break
    return True

#: Supported formats
FORMATS = (".sldprt", ".sldasm", ".slddrw", ".slddrt")

for ext in FORMATS:
    ThumbnailersManager.register(ext, sw_thumbnailer)
