import os.path
import tarfile
import itertools
from cStringIO import StringIO
import struct, time, sys
import binascii, stat
from zipfile import ZipInfo, ZIP_STORED, ZIP_DEFLATED, LargeZipFile, ZIP64_LIMIT

try:
    import zlib # We may need its compression method
    crc32 = zlib.crc32
except ImportError:
    zlib = None
    crc32 = binascii.crc32

def get_available_name(name, exiting_files):
    """
    """
    dir_name, file_name = os.path.split(name)
    file_root, file_ext = os.path.splitext(file_name)
    # If the filename already exists, add an underscore and a number (before
    # the file extension, if one exists) to the filename until the generated
    # filename doesn't exist.
    count = itertools.count(1)
    while name in exiting_files:
        # file_ext includes the dot.
        name = os.path.join(dir_name, "%s_%s%s" % (file_root, count.next(), file_ext))

    return name

#: True if files are compressed or not according to their extension
ZIP_AUTO = -1

#: formats that are stored uncompressed
STORED_FORMATS = set((
    "zip", "gz", "bz2", "tgz", "xz", "rar", ".zipx", # archives
    "png", "gif", "jpg", "jpeg", "svgz", # images
    "odt", "odf", "ods", "odm", "ott", "odp", "otp", # openDocument
    "odg", "odf",
    "docx", "docm", "xlsx", "xlsm", "pptx", "pptm", "dotx", # openXML
    "flac", "ogg", "mp3", "m4a", "ace", "aac", "m4p", "mpa", # audio
    "mp2", "ra", "rm",
    "avi", "dat", "mpeg", "mpg", "mkv", "mov", "ogg", "wmv", # video
    "flv", "3gp", "aaf", "ram", 
))

# constants taken from zipfile module

ZIP_FILECOUNT_LIMIT = 1 << 16
ZIP_MAX_COMMENT = (1 << 16) - 1
structCentralDir = "<4s4B4HL2L5H2L"
stringCentralDir = "PK\001\002"
sizeCentralDir = struct.calcsize(structCentralDir)
structEndArchive = "<4s4H2LH"
stringEndArchive = "PK\005\006"
sizeEndCentDir = struct.calcsize(structEndArchive)

# The "Zip64 end of central directory" record, magic number, size, and indices
# (section V.G in the format document)
structEndArchive64 = "<4sQ2H2L4Q"
stringEndArchive64 = "PK\x06\x06"
sizeEndCentDir64 = struct.calcsize(structEndArchive64)

# The "Zip64 end of central directory locator" structure, magic number, and size
structEndArchive64Locator = "<4sLQL"
stringEndArchive64Locator = "PK\x06\x07"
sizeEndCentDir64Locator = struct.calcsize(structEndArchive64Locator)

class IterZipFile:
    """ A write-only ZipFile that does not write to a file but yields
    its output.

    Example::
        
        z = IterZipFile()
        for buf in z.write(filename, arcname):
            # do stuff with buf
        for buf in z.close():
            # do stuff with buf

    The code is mostly based on :class:`zipfile.ZipFile`.

    :param compression: ZIP_STORED (no compression) or ZIP_DEFLATED (requires zlib)
                        or ZIP_AUTO (compression or not according to the filename).
    :param allowZip64: if True ZipFile will create files with ZIP64 extensions when
                    needed, otherwise it will raise an exception when this would
                    be necessary.
    """

    def __init__(self, compression=ZIP_AUTO, allowZip64=False):

        if compression == ZIP_STORED:
            pass
        elif compression in (ZIP_DEFLATED, ZIP_AUTO):
            if not zlib:
                raise RuntimeError,\
                      "Compression requires the (missing) zlib module"
        else:
            raise RuntimeError, "That compression method is not supported"

        self._allowZip64 = allowZip64
        self.debug = 0  # Level of printing: 0 through 3
        self.NameToInfo = {}    # Find file info given name
        self.filelist = []      # List of ZipInfo instances for archive
        self.compression = compression  # Method of compression
        self.mode = key = "w"
        self.comment = ''
        self.tell = 0

    def _writecheck(self, zinfo):
        """Check for errors before writing a file to the archive."""
        if zinfo.filename in self.NameToInfo:
            if self.debug:      # Warning for duplicate names
                print "Duplicate name:", zinfo.filename
        if zinfo.compress_type == ZIP_DEFLATED and not zlib:
            raise RuntimeError, \
                  "Compression requires the (missing) zlib module"
        if zinfo.compress_type not in (ZIP_STORED, ZIP_DEFLATED):
            raise RuntimeError, \
                  "That compression method is not supported"
        if zinfo.file_size > ZIP64_LIMIT:
            if not self._allowZip64:
                raise LargeZipFile("Filesize would require ZIP64 extensions")
        if zinfo.header_offset > ZIP64_LIMIT:
            if not self._allowZip64:
                raise LargeZipFile("Zipfile size would require ZIP64 extensions")

    def write(self, filename, arcname=None, compress_type=None):
        """Put the bytes from filename into the archive under the name
        arcname."""

        st = os.stat(filename)
        isdir = stat.S_ISDIR(st.st_mode)
        mtime = time.localtime(st.st_mtime)
        date_time = mtime[0:6]
        # Create ZipInfo instance to store file information
        if arcname is None:
            arcname = filename
        arcname = os.path.normpath(os.path.splitdrive(arcname)[1])
        while arcname[0] in (os.sep, os.altsep):
            arcname = arcname[1:]
        if isdir:
            arcname += '/'
        zinfo = ZipInfo(arcname, date_time)
        zinfo.external_attr = (st[0] & 0xFFFF) << 16L      # Unix attributes
        if self.compression == ZIP_AUTO:
            ext = os.path.splitext(filename)[1].lower()
            compression = ZIP_STORED if ext and ext[1:] in STORED_FORMATS \
                    else ZIP_DEFLATED
        else:
            compression = self.compression
        if compress_type is None:
            zinfo.compress_type = compression
        else:
            zinfo.compress_type = compress_type

        zinfo.file_size = st.st_size
        zinfo.flag_bits |= 0x08
        zinfo.header_offset = self.tell    # Start of header bytes

        self._writecheck(zinfo)
        self._didModify = True

        if isdir:
            zinfo.file_size = 0
            zinfo.compress_size = 0
            zinfo.CRC = 0
            self.filelist.append(zinfo)
            self.NameToInfo[zinfo.filename] = zinfo
            header = zinfo.FileHeader()
            yield header
            self.tell += len(header)
            return

        fp = open(filename, "rb")
        # Must overwrite CRC and sizes with correct data later
        zinfo.CRC = CRC = 0
        zinfo.compress_size = compress_size = 0
        zinfo.file_size = file_size = 0
        header = zinfo.FileHeader()
        yield header
        self.tell += len(header)
        if zinfo.compress_type == ZIP_DEFLATED:
            cmpr = zlib.compressobj(zlib.Z_DEFAULT_COMPRESSION,
                 zlib.DEFLATED, -15)
        else:
            cmpr = None
        while 1:
            buf = fp.read(1024 * 8)
            if not buf:
                break
            file_size = file_size + len(buf)
            CRC = crc32(buf, CRC) & 0xffffffff
            if cmpr:
                buf = cmpr.compress(buf)
                compress_size = compress_size + len(buf)
            yield buf
        fp.close()
        if cmpr:
            buf = cmpr.flush()
            compress_size = compress_size + len(buf)
            yield buf
            zinfo.compress_size = compress_size
        else:
            zinfo.compress_size = file_size
        self.tell += zinfo.compress_size
        zinfo.CRC = CRC
        zinfo.file_size = file_size
        # write the data descriptor
        data_descriptor =  struct.pack("<LLL", zinfo.CRC, zinfo.compress_size,
              zinfo.file_size)
        yield data_descriptor
        self.tell += len(data_descriptor)
        self.filelist.append(zinfo)
        self.NameToInfo[zinfo.filename] = zinfo

    def close(self):
        """Close the file, and for mode "w" and "a" write the ending
        records."""

        count = 0
        pos1 = self.tell
        for zinfo in self.filelist:         # write central directory
            count = count + 1
            dt = zinfo.date_time
            dosdate = (dt[0] - 1980) << 9 | dt[1] << 5 | dt[2]
            dostime = dt[3] << 11 | dt[4] << 5 | (dt[5] // 2)
            extra = []
            if zinfo.file_size > ZIP64_LIMIT \
                    or zinfo.compress_size > ZIP64_LIMIT:
                extra.append(zinfo.file_size)
                extra.append(zinfo.compress_size)
                file_size = 0xffffffff
                compress_size = 0xffffffff
            else:
                file_size = zinfo.file_size
                compress_size = zinfo.compress_size

            if zinfo.header_offset > ZIP64_LIMIT:
                extra.append(zinfo.header_offset)
                header_offset = 0xffffffffL
            else:
                header_offset = zinfo.header_offset

            extra_data = zinfo.extra
            if extra:
                # Append a ZIP64 field to the extra's
                extra_data = struct.pack(
                        '<HH' + 'Q'*len(extra),
                        1, 8*len(extra), *extra) + extra_data

                extract_version = max(45, zinfo.extract_version)
                create_version = max(45, zinfo.create_version)
            else:
                extract_version = zinfo.extract_version
                create_version = zinfo.create_version

            try:
                filename, flag_bits = zinfo._encodeFilenameFlags()
                centdir = struct.pack(structCentralDir,
                 stringCentralDir, create_version,
                 zinfo.create_system, extract_version, zinfo.reserved,
                 flag_bits, zinfo.compress_type, dostime, dosdate,
                 zinfo.CRC, compress_size, file_size,
                 len(filename), len(extra_data), len(zinfo.comment),
                 0, zinfo.internal_attr, zinfo.external_attr,
                 header_offset)
            except DeprecationWarning:
                print >>sys.stderr, (structCentralDir,
                 stringCentralDir, create_version,
                 zinfo.create_system, extract_version, zinfo.reserved,
                 zinfo.flag_bits, zinfo.compress_type, dostime, dosdate,
                 zinfo.CRC, compress_size, file_size,
                 len(zinfo.filename), len(extra_data), len(zinfo.comment),
                 0, zinfo.internal_attr, zinfo.external_attr,
                 header_offset)
                raise
            yield centdir
            yield filename
            yield extra_data
            yield zinfo.comment
            self.tell += len(centdir) + len(filename) + len(extra_data) + len(zinfo.comment)

        pos2 = self.tell
        # Write end-of-zip-archive record
        centDirCount = count
        centDirSize = pos2 - pos1
        centDirOffset = pos1
        if (centDirCount >= ZIP_FILECOUNT_LIMIT or
            centDirOffset > ZIP64_LIMIT or
            centDirSize > ZIP64_LIMIT):
            # Need to write the ZIP64 end-of-archive records
            zip64endrec = struct.pack(
                    structEndArchive64, stringEndArchive64,
                    44, 45, 45, 0, 0, centDirCount, centDirCount,
                    centDirSize, centDirOffset)
            yield zip64endrec

            zip64locrec = struct.pack(
                    structEndArchive64Locator,
                    stringEndArchive64Locator, 0, pos2, 1)
            yield zip64locrec
            centDirCount = min(centDirCount, 0xFFFF)
            centDirSize = min(centDirSize, 0xFFFFFFFF)
            centDirOffset = min(centDirOffset, 0xFFFFFFFF)

        # check for valid comment length
        if len(self.comment) >= ZIP_MAX_COMMENT:
            if self.debug > 0:
                msg = 'Archive comment is too long; truncating to %d bytes' \
                      % ZIP_MAX_COMMENT
            self.comment = self.comment[:ZIP_MAX_COMMENT]

        endrec = struct.pack(structEndArchive, stringEndArchive,
                             0, 0, centDirCount, centDirCount,
                             centDirSize, centDirOffset, len(self.comment))
        yield endrec
        yield self.comment


def generate_tarfile(files):
    """
    Returns a generator that yields *files* as a tar file.
    
    This generator does **not** create temporary files and is designed to not
    consume too much memory so it can be used to serve efficiently a tar file
    of large files.

    :param files: a sequence of class:`.DocumentFile`
    """
    fake_file = StringIO()
    tf = tarfile.open(mode= "w", fileobj=fake_file)
    filenames = set()
    for df in files:
        # yields the header
        filename = get_available_name(df.filename, filenames)
        filenames.add(filename)
        info = tf.gettarinfo(df.file.path, filename)
        f, size = df.document.get_leaf_object().get_content_and_size(df)
        # change the name of the owner
        info.uname = info.gname = df.document.owner.username
        info.size = size
        yield info.tobuf()
        # yields the content of the file
        try:
            s = f.read(512)
            while s:
                yield s
                s = f.read(512)
            yield s
            blocks, remainder = divmod(info.size, tarfile.BLOCKSIZE)
            if remainder > 0:
                yield (tarfile.NUL * (tarfile.BLOCKSIZE - remainder))
        finally:
            f.close()
    # yields the nul blocks that mark the end of the tar file
    yield (tarfile.NUL * tarfile.BLOCKSIZE * 2)


def generate_zipfile(files):
    """
    Returns a generator that yields *files* as a zip file.
    
    This generator does **not** create temporary files and is designed to not
    consume too much memory so it can be used to serve efficiently a tar file
    of large files.

    :param files: a sequence of class:`.DocumentFile`
    :param compressed: ``True`` if files should be compressed (default: True)
    """
    zf = IterZipFile()
    filenames = set()
    for df in files:
        filename = get_available_name(df.filename, filenames)
        filenames.add(filename)
        f, size = df.document.get_leaf_object().get_content_and_size(df)
        path = f.name
        try:
            for s in zf.write(path, filename):
                yield s
        finally:
            f.close()
    for s in zf.close():
        yield s

_generators = {
    "zip" : generate_zipfile,
    "tar" : generate_tarfile,
}

#: List of available archive formats (currently: ``zip`` and ``tar``).
ARCHIVE_FORMATS = _generators.keys()

def generate_archive(files, format):
    return _generators[format](files)

