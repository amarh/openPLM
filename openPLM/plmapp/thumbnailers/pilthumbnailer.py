import Image

from base import ThumbnailersManager

def pil_thumbnailer(input_path, original_filename, output_path):
    """
    Thumbnailer that uses PIL to generate a thumbnail from an
    image.
    """
    im = Image.open(input_path)
    im.thumbnail(ThumbnailersManager.THUMBNAIL_SIZE, Image.ANTIALIAS)
    im.save(output_path)
    return False

Image.init()
for ext, name in Image.EXTENSION.iteritems():
    if name in Image.OPEN:
        ThumbnailersManager.register(ext, pil_thumbnailer)
