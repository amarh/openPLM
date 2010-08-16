try:
    import openPLM.plmapp.models as models
    from openPLM.plmapp.exceptions import RevisionError, LockError, UnlockError, \
        AddFileError, DeleteFileError
except (ImportError, AttributeError):
    import plmapp.models as models
    from plmapp.exceptions import RevisionError, LockError, UnlockError, \
        AddFileError, DeleteFileError

class UserController(object):
    u"""
    Object used to manage a :class:`~django.contrib.auth.models.User` and store his 
    modification in an history
    
    :attributes:
        .. attribute:: object

            The :class:`~django.contrib.auth.models.User` managed by the controller

    :param obj: managed object
    :type obj: an instance of :class:`~django.contrib.auth.models.User`
    :param user: user who modify *obj*
    :type user: :class:`~django.contrib.auth.models.User` 

    .. note::
        This class does not inherit from :class:`PLMObjectController`.

    """

    def __init__(self, obj, user):
        self.object = obj
        self._user = user
        self.__histo = ""
        self.creator = user
        self.owner = user
        self.mtime = obj.last_login
        self.ctime = obj.date_joined


    def update_from_form(self, form):
        u"""
        Updates :attr:`object` from data of *form*
        
        This method raises :exc:`ValueError` if *form* is invalid.
        """
        if form.is_valid():
            need_save = False
            for key, value in form.cleaned_data.iteritems():
                if key not in ["username"]:
                    setattr(self, key, value)
                    need_save = True
            if need_save:
                self.save()
        else:
            raise ValueError("form is invalid")

    def __setattr__(self, attr, value):
        if hasattr(self, "object") and hasattr(self.object, attr) and \
           not attr in self.__dict__:
            old_value = getattr(self.object, attr)
            setattr(self.object, attr, value)
            field = self.object._meta.get_field(attr).verbose_name
            message = "%(field)s : changes from '%(old)s' to '%(new)s'" % \
                    {"field" : field, "old" : old_value, "new" : value}
            self.__histo += message + "\n"
        else:
            super(UserController, self).__setattr__(attr, value)

    def __getattr__(self, attr):
        obj = object.__getattribute__(self, "object")
        if hasattr(self, "object") and hasattr(obj, attr) and \
           not attr in self.__dict__:
            return getattr(obj, attr)
        else:
            return object.__getattribute__(self, attr)

    def save(self, with_history=True):
        u"""
        Saves :attr:`object` and records its history in the database.
        If *with_history* is False, the history is not recorded.
        """
        self.object.save()
        if self.__histo and with_history:
            self._save_histo("Modify", self.__histo) 
            self.__histo = ""

    def _save_histo(self, action, details):
        # TODO : use the correct model
        pass
        #histo = models.History()
        #histo.plmobject = self.object
        #histo.action = action
        #histo.details = details 
        #histo.user = self._user
        #histo.save()
    
    @property
    def plmobject_url(self):
        return "/user/%s/" % self.object.username

    @property
    def attributes(self):
        u"Attributes to display in `Attributes view`"
        return ["first_name", "last_name", "email",  "creator", "owner",
                "ctime", "mtime"]

    @property
    def menu_items(self):
        "menu items to choose a view"
        return ["attributes", "lifecycle", "history"]

    @classmethod
    def excluded_creation_fields(cls):
        "Returns fields which should not be available in a creation form"
        return ["owner", "creator", "ctime", "mtime"]

