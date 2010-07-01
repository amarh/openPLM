class HandlersManager(object):
    _handlers = {}

    @classmethod
    def register(cls, typename, handler):
        l = cls._handlers.get(typename, [])
        l.append(handler)
        cls._handlers[typename] = l

    @classmethod
    def get_best_handler(cls, typename):
        return cls._handlers[typename][0]

    @classmethod
    def get_all_handlers(cls, typename):
        return list(cls._handlers[typename])

    @classmethod
    def get_all_supported_types(cls):
        return cls._handlers.keys()

class FileHandler(object):

    def __init__(self, path, filename):
        self._path = path
        self._filename = filename
        self._is_valid = False

    def _set_valid(self):
        self._is_valid = True

    def _set_invalid(self):
        self._is_valid = False
    
    def is_valid(self):
        return self._is_valid

    @property
    def attributes(self):
        return []
