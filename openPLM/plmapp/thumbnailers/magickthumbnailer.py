import subprocess

import sys
mswindows = (sys.platform == "win32")

from base import ThumbnailersManager

def limit_resources():
    """
    Limits the process execution time to 60 seconds.
    """
    try:
        from resource import getrlimit, setrlimit, RLIMIT_CPU
    except ImportError:
        return
    else:
        def _setrlimit(key, value):
            try:
                soft, hard = getrlimit(key)
                # Change soft limit
                if hard != -1:
                    soft = min(value, hard)
                else:
                    soft = value
            except ValueError:
                hard = -1
            setrlimit(key, (soft, hard))
        _setrlimit(RLIMIT_CPU, 60)


def magick_thumbnailer(input_path, original_filename, output_path):
    """
    Thumbnailer that calls :command:`convert` (from ImageMagick) to generate
    a thumbnail.
    """
    if mswindows:
        preexec_fn = None
    else:
        preexec_fn = limit_resources

    args = ["convert", "-format", "png",
            "-thumbnail", "%dx%d" % ThumbnailersManager.THUMBNAIL_SIZE,
            u"%s[0]" % input_path, output_path]
    subprocess.check_call(args, preexec_fn=preexec_fn)
    return False

#: Supported formats (if all ImageMagick decoders are installed)
FORMATS = (".3fr", ".a", ".ai", ".art", ".arw", ".avi", ".avs", ".b",
    ".bgr", ".bgra", ".bmp", ".brg", ".c", ".cal", ".cals", ".caption",
    ".cin", ".cmyk", ".cmyka", ".cr2", ".crw", ".cur", ".cut", ".dcm",
    ".dcr", ".dcx", ".dds", ".dfont", ".djvu", ".dng", ".dot", ".dpx",
    ".epdf", ".epi", ".eps", ".epsf", ".epsi", ".ept", ".ept2", ".ept3",
    ".erf", ".exr", ".fax", ".fits", ".fractal", ".fts", ".g", ".g3",
    ".gbr", ".gif", ".gif87", ".gradient", ".gray", ".grb", ".group4", ".hald",
    ".hrz", ".icb", ".ico", ".icon", ".inline", ".ipl", ".j2c", ".jng",
    ".jp2", ".jpc", ".jpeg", ".jpg", ".jpx", ".k", ".k25", ".kdc",
    ".label", ".m", ".m2v", ".m4v", ".map", ".mat", ".miff", ".mng",
    ".mono", ".mov", ".mp4", ".mpc", ".mpeg", ".mpg", ".mrw", ".msl",
    ".msvg", ".mtv", ".mvg", ".nef", ".null", ".o", ".orf", ".otb",
    ".otf", ".pal", ".palm", ".pam", ".pattern", ".pbm", ".pcd", ".pcds",
    ".pcl", ".pct", ".pcx", ".pdb", ".pdf", ".pdfa", ".pef", ".pes",
    ".pfa", ".pfb", ".pfm", ".pgm", ".pgx", ".picon", ".pict", ".pix",
    ".pjpeg", ".plasma", ".png", ".png24", ".png32", ".png8", ".pnm", ".ppm",
    ".ps", ".psb", ".psd", ".ptif", ".pwp", ".r", ".raf", ".ras",
    ".rbg", ".rgb", ".rgba", ".rgbo", ".rla", ".rle", ".scr", ".sct",
    ".sfw", ".sgi", ".sr2", ".srf", ".stegano", ".sun", ".svg", ".svgz",
    ".text", ".tga", ".tiff", ".tile", ".tim", ".ttc", ".ttf", ".txt",
    ".uyvy", ".vda", ".vicar", ".vid", ".viff", ".vst", ".wbmp", ".wmf",
    ".wmv", ".wmz", ".wpg", ".x", ".x3f", ".xbm", ".xc", ".xcf",
    ".xpm", ".xps", ".xv", ".xwd", ".y", ".ycbcr", ".ycbcra", ".yuv")

# some formats may not be available, but it is simpler/faster to let
# imagemagick fail than checking available format.
for ext in FORMATS:
    ThumbnailersManager.register(ext, magick_thumbnailer)
