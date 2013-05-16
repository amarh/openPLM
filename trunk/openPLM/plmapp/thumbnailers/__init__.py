
"""
This module contains utilities to generate a thumbnail from a file.

Thumbnailers are registered with :class:`.ThumbnailersManager`.

"""

import os.path
import Image

from base import ThumbnailersManager
from openPLM.plmapp.utils import get_ext

# import "official" thumbnailers
import pilthumbnailer
import odfthumbnailer
import magickthumbnailer
import jfifthumbnailer
import pngthumbnailer
import swthumbnailer

from openPLM.plmapp.models import DocumentFile, thumbnailfs
from djcelery_transactions import task

@task(name="openPLM.plmapp.thumbnailers.generate_thumbnail",
      ignore_result=True, soft_time_limit=60, time_limit=65)
def generate_thumbnail(doc_file_id):
    """
    Celery task that tries to generate a thumbnail for a :class:`.DocumentFile`.

    If it succeed, this function modifies the :attr:`.DocumentFile.thumbnail`
    attribute.  The stored value follow the following pattern
    :samp:`{doc_file_id}.png`.

    :param doc_file_id: id of the :class:`.DocumentFile`.
    """
    doc_file = DocumentFile.objects.get(id=doc_file_id)
    ext = os.path.splitext(doc_file.filename)[1].lower()
    ext2 = get_ext(doc_file.filename)
    name = "%s.png" % (doc_file_id)
    thumbnail_path = thumbnailfs.path(name)
    generated = resize = False
    thumbnailers = ThumbnailersManager.get_all_thumbnailers(ext)[:]
    if ext2 != ext:
        thumbnailers.extend(ThumbnailersManager.get_all_thumbnailers(ext2))
    for thumbnailer in thumbnailers:
        try:
            resize = thumbnailer(doc_file.file.path, doc_file.filename, thumbnail_path)
        except Exception, e:
            # let another thumbnailer do the job
            if os.path.exists(thumbnail_path):
                # this file may be corrupted
                os.remove(thumbnail_path)
        else:
            if os.path.exists(thumbnail_path):
                doc_file.thumbnail = os.path.basename(thumbnail_path)
                doc_file.no_index = True
                doc_file.save(update_fields=("thumbnail",))
                generated = True
                break
    if generated and resize:
        image = Image.open(thumbnail_path)
        image.thumbnail(ThumbnailersManager.THUMBNAIL_SIZE, Image.ANTIALIAS)
        image.save(doc_file.thumbnail.path)

