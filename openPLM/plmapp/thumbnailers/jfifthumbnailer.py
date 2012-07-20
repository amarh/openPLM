"""
.. versionadded:: 1.1

This module adds an optimist thumbnailer for some files which contain
a JPEG thumbnails.

This formats are:

    * CATIA file (CATPart, CATProduct, CATDrawing)
    * Pro Engineer file (prt, asm)


How it works
=============

Some files may contain a thumbnail. This thumbnail is
stored somewhere in the file as a JPEG image.
So the idea is to try to find a JPEG image in the original
file and hope it is a valid image (and the thumbnail).

All JPEG file starts with a magic number (``0xFFD8``).
This thumbnailer locates this magic number and tries to read
the image with PIL. If it succeeds, it assumes it is the thumbnail.
If it fails, it tries to find another magic number and retries.
"""


import Image

from base import ThumbnailersManager
from openPLM.plmapp.utils import SeekedFile


def jfif_thumbnailer(input_path, original_filename, output_path):
    """
    Thumbnailer for files which contain a JPEG thumbnail.
    """
    # the file must be opened in binary mode
    with open(input_path, 'rb') as cad:
        def seek():
            " Seek to the possible start of a JPEG file"
            c1, c2 = cad.read(1), cad.read(2)
            while c1 + c2 != '\xff\xd8':
                c1 = c2
                c2 = cad.read(1)
                if c2 == '':
                    # end of file, raises an exception so that the thumbnailer fails
                    raise Exception()
            cad.seek(-2, 1)
        done = False
        while not done:
            seek()
            try: 
                im = Image.open(SeekedFile(cad))
            except IOError:
                # not a JPEG, goes forward and looks up for another
                # magic number
                cad.seek(3, 1)
            else:
                # looks good, save the image
                im.thumbnail(ThumbnailersManager.THUMBNAIL_SIZE, Image.ANTIALIAS)
                im.save(output_path)
                done = True
    return False

CATIA_FILES = ("catpart", "catproduct", "catdrawing")
PRO_ENGINEER_FILES = ("asm", "prt")
FILES = CATIA_FILES + PRO_ENGINEER_FILES
for ext in FILES:
    ThumbnailersManager.register("." + ext, jfif_thumbnailer)
