"""
.. versionadded:: 1.1

This module adds an optimist thumbnailer for some files which contain
a PNG thumbnails.

These formats are:

    * Google Sketch Up (skp)


How it works
=============

Some files may contain a thumbnail. This thumbnail is
stored somewhere in the file as a PNG image.
So the idea is to try to find a PNG image in the original
file and hope it is a valid image (and the thumbnail).

All PNG file starts with a magic number (``89 50 4E 47 0D 0A 1A 0A``).
This thumbnailer locates this magic number and tries to read
the image with PIL. If it succeeds, it assumes it is the thumbnail.
If it fails, it tries to find another magic number and retries.
"""


import Image

from base import ThumbnailersManager
from openPLM.plmapp.utils import SeekedFile

PNG_MAGIC_NUMBER = '\x89PNG\r\n\x1a\n'

def png_thumbnailer(input_path, original_filename, output_path):
    """
    Thumbnailer for files which contain a PNG thumbnail.
    """
    # the file must be opened in binary mode
    with open(input_path, 'rb') as cad:
        def seek():
            t = cad.tell()
            data = cad.read(1024)
            pos = data.find(PNG_MAGIC_NUMBER)
            while pos == -1:
                data = cad.read(1024)
                # end of file, raises an exception so that the thumbnailer fails
                if not data:
                    raise Exception()
                pos = data.find(PNG_MAGIC_NUMBER)
            cad.seek(t + pos)

        done = False
        while not done:
            seek()
            try: 
                im = Image.open(SeekedFile(cad))
            except IOError:
                # not a PNG, goes forward and looks up for another
                # magic number
                cad.seek(5, 1)
            else:
                # looks good, save the image
                im.thumbnail(ThumbnailersManager.THUMBNAIL_SIZE, Image.ANTIALIAS)
                im.save(output_path)
                done = True
    return False

FILES = ("skp", # google sketch up
    )
for ext in FILES:
    ThumbnailersManager.register("." + ext, png_thumbnailer)

