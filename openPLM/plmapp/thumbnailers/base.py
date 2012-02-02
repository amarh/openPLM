from collections import defaultdict

class ThumbnailersManager(object):
    """
    The ThumbnailersManager has methods to register a thumbnailer with a
    type of file (an extension with the dot, like ``".pdf"``) and to get a
    thumbnailer from a extension.
    
    A thumbnailer is a function which takes 3 arguments:

        * input_path: path of the input file
        * original_filename: original filename, as uploaded by the user
        * output_path: path where the thumbnail should be saved.

    It returns ``True`` if the generated thumbnail should be resized to
    :attr:`.THUMBNAIL_SIZE`, ``False`` otherwise.

    A thumbnailer must generate a png file. If it fails, it must raise an
    exception.

    In all methods, *extension* should be in lowercase and starts with a dot.
    """
    #: internal dict(extension->Hanfler)
    _thumbnailers = defaultdict(list)
   
    #: thumbnail size
    THUMBNAIL_SIZE = (150, 150)

    @classmethod
    def register(cls, extension, thumbnailer):
        """
        Registers *thumbnailer* for *extension*.
        """
        cls._thumbnailers[extension].append(thumbnailer)

    @classmethod
    def get_best_thumbnailer(cls, extension):
        """
        Gets the best thumbnailer associated to *extension*. The best
        thumbnailer is the first registered thumbnailer for *extension*.
        """
        return cls._thumbnailers[extension][0]

    @classmethod
    def get_all_thumbnailers(cls, extension):
        """
        Returns a list of all thumbnailer associated to *extension*.
        """
        return list(cls._thumbnailers[extension])

    @classmethod
    def get_all_supported_types(cls):
        """
        Returns all supported types (a list of string).
        """
        return cls._thumbnailers.keys()

