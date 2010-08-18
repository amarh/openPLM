"""
This module contains a class called :class:`UserController` which
provides a controller for :class:`~django.contrib.auth.models.User`.
This class is similar to :class:`.PLMObjectController` but some methods
from :class:`.PLMObjectController` are not defined.
"""

from django.core.exceptions import ObjectDoesNotExist
from django.db.models.fields import FieldDoesNotExist

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

    def get_verbose_name(self, attr_name):
        """
        Returns a verbose name for *attr_name*.

        Example::

            >>> ctrl.get_verbose_name("ctime")
            u'date of creation'
        """

        try:
            item = unicode(self.object._meta.get_field(attr_name).verbose_name)
        except FieldDoesNotExist:
            names = {"mtime" : "date of last modification",
                     "ctime" : "date of creation"}
            item = names.get(attr_name, attr_name)
        return item

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
        if hasattr(self, "object"):
            obj = object.__getattribute__(self, "object")
            try:
                profile = obj.get_profile()
            except ObjectDoesNotExist:
                profile = None
        else:
            obj = None
        if obj and (hasattr(obj, attr) or hasattr(profile, attr)) and \
           not attr in self.__dict__:
            obj2 = obj if hasattr(obj, attr) else profile
            old_value = getattr(obj2, attr)
            setattr(obj2, attr, value)
            field = obj2._meta.get_field(attr).verbose_name.capitalize()
            message = "%(field)s : changes from '%(old)s' to '%(new)s'" % \
                    {"field" : field, "old" : old_value, "new" : value}
            self.__histo += message + "\n"
        else:
            super(UserController, self).__setattr__(attr, value)

    def __getattr__(self, attr):
        obj = object.__getattribute__(self, "object")
        try:
            profile = obj.get_profile()
        except ObjectDoesNotExist:
            profile = None
        if hasattr(self, "object") and hasattr(obj, attr) and \
           not attr in self.__dict__:
            return getattr(obj, attr)
        elif profile and hasattr(profile, attr) and not attr in self.__dict__:
            return getattr(profile, attr)
        else:
            return object.__getattribute__(self, attr)

    def save(self, with_history=True):
        u"""
        Saves :attr:`object` and records its history in the database.
        If *with_history* is False, the history is not recorded.
        """
        self.object.save()
        try:
            self.object.get_profile().save()
        except ObjectDoesNotExist:
            pass        
        if self.__histo and with_history:
            self._save_histo("Modify", self.__histo) 
            self.__histo = ""

    def _save_histo(self, action, details):
        histo = models.UserHistory()
        histo.plmobject = self.object
        histo.action = action
        histo.details = details 
        histo.user = self._user
        histo.save()

