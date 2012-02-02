import shutil
import zipfile

from base import ThumbnailersManager

def odf_thumbnailer(input_path, original_filename, output_path):
    """
    Thumbnailer for OpenDocument (odt, ods...) files.
    """
    try:
        zp = zipfile.ZipFile(input_path, 'r')
        image = zp.open("Thumbnails/thumbnail.png")
        with open(output_path, "wb") as of:
            shutil.copyfileobj(image, of)
    except KeyError:
        zp.close()
    except (IOError, zipfile.BadZipfile):
        pass
    return True

for ext in ("odt", "odf", "ods", "odm", "ott", "odp", "otp", "odg", "odf"):
    ThumbnailersManager.register("." + ext, odf_thumbnailer)
