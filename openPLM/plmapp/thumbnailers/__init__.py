
"""
This module contains utilities to generate a thumbnail from a file.

Thumbnailers are registered with :class:`.ThumbnailersManager`.

"""

import os.path
import Image

from base import ThumbnailersManager

# import "official" thumbnailers
import pilthumbnailer
import odfthumbnailer
import magickthumbnailer

from openPLM.plmapp.models import DocumentFile, thumbnailfs
from celery.task import task

@task(ignore_result=True)
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
    name = "%s.png" % (doc_file_id)
    thumbnail_path = thumbnailfs.path(name)
    generated = resize = False
    for thumbnailer in ThumbnailersManager.get_all_thumbnailers(ext):
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
                doc_file.save()
                generated = True
                break
    if generated and resize:
        image = Image.open(thumbnail_path)
        image.thumbnail(ThumbnailersManager.THUMBNAIL_SIZE, Image.ANTIALIAS)
        image.save(doc_file.thumbnail.path)

