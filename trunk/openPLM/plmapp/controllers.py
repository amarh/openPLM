import re
try:
    import openPLM.plmapp.models as models
except AttributeError:
    import plmapp.models as models

_controller_rx = re.compile(r"(?P<type>\w+)Controller")

class MetaController(type):
    controllers_dict = {}
    def __new__(mcs, name, bases, attrs):
        cls = type.__new__(mcs, name, bases, attrs)
        if "MANAGED_TYPE" in attrs:
            managed = attrs["MANAGED_TYPE"].__name__
        else:
            m = _controller_rx.match(name)
            if m:
                managed = m.group("type")
            else:
                # the controller is not interresting
                return cls
        mcs.controllers_dict[managed] = cls
        return cls

    @classmethod
    def get_controller(cls, type_name):
        if type_name in cls.controllers_dict:
            return cls.controllers_dict[type_name]
        else:
            # get his model and return his parent controller
            if type_name == "PLMObject":
                # just a security to prevent an infinite recursion
                return PLMObjectController
            else:
                model = models.get_all_plmobjects()[type_name]
                parents = [p for p in model.__bases__ 
                                if issubclass(p, models.PLMObject)]
                return cls.get_controller(parents[0].__name__)

get_controller = MetaController.get_controller

class PLMObjectController(object):
    u"""
    Object used to manage a :class:`~plmapp.models.PLMObject` and store his 
    modification in an history
    
    :attributes:
        .. attribute:: object

            The :class:`~openPLM.plmapp.models.PLMObject` managed by the controllers

    :param obj: managed object
    :type obj: a subinstance of :class:`~openPLM.plmapp.models.PLMObject`
    :param user: user who modify *obj*
    :type user: :class:`~django.contrib.auth.models.User` 
    """

    __metaclass__ = MetaController

    def __init__(self, obj, user):
        self.object = obj
        self._user = user
        self.__histo = ""

    @classmethod
    def create(cls, reference, type, revision, user, data={}):
        u"""
        This methods build a new :class:`~openPLM.plmapp.models.PLMObject` of type *class_*
        and return a :class:`PLMObjectController` associated to the created object.

        :param reference: reference of the objet
        :param type: type of the object
        :param revision: revision of the object
        :param user: user who creates/owns the object
        :rtype: :class:`PLMObjectController`
        """

        class_ = models.get_all_plmobjects().get(type) 
        # create an object
        obj = class_()
        obj.reference = reference
        obj.type = type
        obj.revision = revision
        obj.owner = user
        obj.creator = user
        if data:
            for key, value in data.iteritems():
                if key not in ["reference", "type", "revision"]:
                    setattr(obj, key, value)
        obj.state = models.get_default_state(obj.lifecycle)
        obj.save()
        res = cls(obj, user)
        # record ceation in history
        infos = {"type" : type, "reference" : reference, "revision" : revision}
        infos.update(data)
        details = ",".join("%s : %s" % (k,v) for k, v in infos.items())
        res._save_histo("Create", details)
        return res
        
    @classmethod
    def create_from_form(cls, form, user):
        u"""
        Creates a :class:`PLMObjectController` from *form* and associates *user*
        as the creator/owner of the PLMObject.
        
        This method raises :exc:`ValueError` if *form* is invalid.

        :param form: a django form associated to a model
        :param user: user who creates/owns the object
        :rtype: :class:`PLMObjectController`
        """
        if form.is_valid():
            ref = form.cleaned_data["reference"]
            type = form.Meta.model.__name__
            rev = form.cleaned_data["revision"]
            obj = cls.create(ref, type, rev, user, form.cleaned_data)
            return obj
        else:
            raise ValueError("form is invalid")
        
    def update_from_form(self, form):
        u"""
        Updates :attr:`object` from data of *form*
        
        This method raises :exc:`ValueError` if *form* is invalid.
        """
        if form.is_valid():
            need_save = False
            for key, value in form.cleaned_data.iteritems():
                if key not in ["reference", "type", "revision"]:
                    setattr(self, key, value)
                    need_save = True
            if need_save:
                self.save()
        else:
            raise ValueError("form is invalid")

    def promote(self):
        u"""
        Promotes :attr:`object` in his lifecycle and writes his promotion in the history
        """
        if self.object.is_promotable():
            state = self.object.state
            lifecycle = self.object.lifecycle
            lcl = lifecycle.to_states_list()
            try:
                new_state = lcl.next_state(state.name)
                self.object.state = models.State.objects.get_or_create(name=new_state)[0]
                self.object.save()
                self._save_histo("Promote",
                                 "change state from %(first)s to %(second)s" % \
                                     {"first" :state.name, "second" : new_state})

            except IndexError:
                # FIXME raises it ?
                pass

    def demote(self):
        u"""
        Demotes :attr:`object` in his lifecycle and writes his demotion in the history
        """
        state = self.object.state
        lifecycle = self.object.lifecycle
        lcl = lifecycle.to_states_list()
        try:
            new_state = lcl.previous_state(state.name)
            self.object.state = models.State.objects.get_or_create(name=new_state)[0]
            self.object.save()
            self._save_histo("Demote", "change state from %(first)s to %(second)s" % \
                    {"first" :state.name, "second" : new_state})
        except IndexError:
            # FIXME raises it ?
            pass

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
            super(PLMObjectController, self).__setattr__(attr, value)

    def __getattr__(self, attr):
        obj = object.__getattribute__(self, "object")
        if hasattr(self, "object") and hasattr(obj, attr) and \
           not attr in self.__dict__:
            return getattr(obj, attr)
        else:
            return object.__getattribute__(self, attr)

    def save(self):
        u"""
        Saves :attr:`object` and write the history in the database
        """
        self.object.save()
        if self.__histo:
            self._save_histo("Modify", self.__histo) 
            self.__histo = ""

    def _save_histo(self, action, details):
        histo = models.History()
        histo.plmobject = self.object
        histo.action = action
        histo.details = details 
        histo.user = self._user
        histo.save()
         

class PartController(PLMObjectController):
    
    def add_child(self, child, quantity, order):
        if isinstance(child, PLMObjectController):
            child = child.object
        # check if child is not a parent
        if child == self.object:
            raise ValueError("Can not add child : child is current object")
        parents = (p[1] for p in self.get_parents(-1))
        if child in parents:
            raise ValueError("Can not add child %s to %s, it is a parent" %
                                (child, self.object))
        # check if child is not already a direct child
        if child in self.get_children(1):
            raise ValueError("%s is already a child of %s" % (child, self.object))
        # create the link
        link = models.ParentChildLink()
        link.parent = self.object
        link.child = child
        link.quantity = quantity
        link.order = order
        link.save()
        # records creation in history
        self._save_histo(link.ACTION_NAME,
                         "parent : %s\nchild : %s" % (self.object, child))

    def delete_child(self, child):
        if isinstance(child, PLMObjectController):
            child = child.object
        link = models.ParentChildLink.objects.get(object1=self.object, object2=child)
        link.delete()
        self._save_histo("Delete - %s" % link.ACTION_NAME, "child : %s" % child)

    def get_children(self, max_level=1, current_level=1):
        if max_level != -1 and current_level > max_level:
            return []
        links = models.ParentChildLink.objects.filter(object1=self.object)
        res = []
        for link in links:
            res.append((current_level, link.child, link.quantity, link.order))
            pc = PartController(link.child, self._user)
            res.extend(pc.get_children(max_level, current_level + 1))
        return res
    
    def get_parents(self, max_level=1, current_level=1):
        if max_level != -1 and current_level > max_level:
            return []
        links = models.ParentChildLink.objects.filter(object2=self.object)
        res = []
        for link in links:
            res.append((current_level, link.parent, link.quantity, link.order))
            pc = PartController(link.parent, self._user)
            res.extend(pc.get_parents(max_level, current_level + 1))
        return res



class DocumentController(PLMObjectController):
    pass

class PlasticPartController(PartController):
    pass

class RedPlasticPartController(PlasticPartController):
    pass


