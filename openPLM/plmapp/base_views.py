import functools
import traceback
import sys

from django.shortcuts import get_object_or_404
from django.utils import simplejson
from django.core.mail import mail_admins
from django.utils.translation import ugettext as _
from django.http import HttpResponse
from django.contrib.auth.models import User

import openPLM.plmapp.models as models

from openPLM.plmapp.controllers import get_controller
from openPLM.plmapp.user_controller import UserController


def get_obj(obj_type, obj_ref, obj_revi, user):
    """
    Get type, reference and revision of an object and return the related controller
    
    :param obj_type: :attr:`.PLMObject.type`
    :type obj_type: str
    :param obj_ref: :attr:`.PLMObject.reference`
    :type obj_ref: str
    :param obj_revi: :attr:`.PLMObject.revision`
    :type obj_revi: str
    :return: a :class:`PLMObjectController` or a :class:`UserController`
    """
    if obj_type == 'User':
        obj = get_object_or_404(User, username=obj_ref)
        controller_cls = UserController
    else:
        obj = get_object_or_404(models.PLMObject, type=obj_type,
                                reference=obj_ref,
                                revision=obj_revi)
        # guess what kind of PLMObject (Part, Document) obj is
        cls = models.PLMObject
        find = True
        while find:
            find = False
            for c in cls.__subclasses__():
                if hasattr(obj, c.__name__.lower()):
                    cls  = c
                    obj = getattr(obj, c.__name__.lower())
                    find = True
        controller_cls = get_controller(obj_type)
    return controller_cls(obj, user)


def json_view(func, API_VERSION=""):
    """
    Decorator which converts the result from *func* into a json response.
    
    The result from *func* must be serializable by :mod:`django.utils.simple_json`
    
    This decorator automatically adds a ``result`` field to the response if it
    was not present. Its value is ``'ok'`` if no exception was raised, and else,
    it is ``'error'``. In that case, a field ``'error'`` is had with a short
    message describing the exception.
    """
    @functools.wraps(func)
    def wrap(request, *a, **kw):
        try:
            response = dict(func(request, *a, **kw))
            if 'result' not in response:
                response['result'] = 'ok'
        except KeyboardInterrupt:
            # Allow keyboard interrupts through for debugging.
            raise
        except Exception, e:
            print e
            #Mail the admins with the error
            exc_info = sys.exc_info()
            subject = 'JSON view error: %s' % request.path
            try:
                request_repr = repr(request)
            except:
                request_repr = 'Request repr() unavailable'
            message = 'Traceback:\n%s\n\nRequest:\n%s' % (
                '\n'.join(traceback.format_exception(*exc_info)),
                request_repr,
                )
            mail_admins(subject, message, fail_silently=True)
            #Come what may, we're returning JSON.
            msg = _('Internal error') + ': ' + str(e)
            response = {'result' : 'error', 'error' : msg}
        response["api_version"] = API_VERSION
        json = simplejson.dumps(response)
        return HttpResponse(json, mimetype='application/json')
    return wrap


def get_obj_by_id(obj_id, user):
    u"""
    Returns an adequate controller for the object identify by *obj_id*.
    The returned controller is instanciate with *user* as the user
    who modify the object.

    :param obj_id: id of a :class:`.PLMObject`
    :param user: a :class:`.django.contrib.auth.models.User`
    :return: a subinstance of a :class:`.PLMObjectController`
    """

    obj = get_object_or_404(models.PLMObject, id=obj_id)
    obj = models.get_all_plmobjects()[obj.type].objects.get(id=obj_id)
    return get_controller(obj.type)(obj, user)

def object_to_dict(plmobject):
    """
    Returns a dictionary representing *plmobject*. The returned dictionary
    respects the format described in :ref`http-api-object`
    """
    return dict(id=plmobject.id, name=plmobject.name, type=plmobject.type,
                revision=plmobject.revision, reference=plmobject.reference)

