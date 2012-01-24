from functools import wraps

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect

import gdata.client
from oauth2client.django_orm import Storage
from oauth2client.client import OAuth2WebServerFlow

import openPLM.plmapp.views.main as pviews
from openPLM.plmapp.base_views import handle_errors, get_generic_data

from openPLM.gdoc.models import CredentialsModel, FlowModel
from openPLM.gdoc.models import GoogleDocument, GoogleDocumentController
from openPLM.gdoc.forms import get_gdoc_creation_form
from openPLM.gdoc.gutils import get_gclient, SCOPES, USER_AGENT

STEP2_URI = '%s/oauth2callback'


def oauth2_required(func):
    """
    Decorator that ensures that a view is called with a valid 
    google client.

    The function *func* must have the following definition::

        def function(request, client, what you want):
            return an HttpResponse

    """
    @wraps(func)
    def wrapper(request, *args, **kwargs):
        storage = Storage(CredentialsModel, 'id', request.user,
                'credential')
        credential = storage.get()
        if credential is None or credential.access_token_expired:
            flow = OAuth2WebServerFlow(
                client_id=settings.GOOGLE_CONSUMER_KEY,
                client_secret=settings.GOOGLE_CONSUMER_SECRET,
                scope=SCOPES,
                user_agent=USER_AGENT,
                state=request.build_absolute_uri()
                )
            protocol = 'https://' if request.is_secure() else "http://"
            uri = STEP2_URI % request.get_host()
            authorize_url = flow.step1_get_authorize_url(protocol + uri)
            flow_model = FlowModel(id=request.user, flow=flow)
            flow_model.save()
            return HttpResponseRedirect(authorize_url)

        client = get_gclient(credential)
        return func(request, client, *args, **kwargs)
    return wrapper

@login_required
def auth_return(request):
    try:
        f = FlowModel.objects.get(id=request.user)
        credential = f.flow.step2_exchange(request.REQUEST)
        storage = Storage(CredentialsModel, 'id', request.user, 'credential')
        storage.put(credential)
        f.delete()
        return HttpResponseRedirect(request.GET.get('state', '/'))
    except FlowModel.DoesNotExist:
        pass

@oauth2_required
@handle_errors
def create_gdoc(request, client):
    """
    Creation view of a :class:`.GoogleDocument`.
    """

    obj, ctx = get_generic_data(request)
    
    if request.method == 'GET':
        creation_form = get_gdoc_creation_form(request.user, client)
    elif request.method == 'POST':
        creation_form = get_gdoc_creation_form(request.user, client,
                request.POST)
        if creation_form.is_valid():
            user = request.user
            ctrl = GoogleDocumentController.create_from_form(creation_form, user)
            return HttpResponseRedirect(ctrl.plmobject_url)
    ctx.update({
        'creation_form': creation_form,
        'object_type': "GoogleDocument",
    })
    return pviews.r2r('DisplayObject4creation.htm', ctx, request)
pviews.register_creation_view(GoogleDocument, create_gdoc)

@oauth2_required
@handle_errors
def display_files(request, client, obj_type, obj_ref, obj_revi):
    """
    Files page of a GoogleDocument. 
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    
    if not hasattr(obj, "files"):
        raise TypeError()
    try:
        entry = client.get_resource_by_id(obj.resource_id)
        edit_uri = ""
        for link in entry.link:
            if link.rel == 'alternate':
                edit_uri = link.href
                break
        uri = client._get_download_uri(entry.content.src)
        ctx.update({
            'resource' : obj.resource_id.split(":", 1)[-1],
            'download_uri' : uri,
            'edit_uri' : edit_uri,
            'error' : False,
            })
    except gdata.client.RequestError:
        ctx['error'] = True
    
    ctx['current_page'] = 'files'
    return pviews.r2r('gdoc_files.htm', ctx, request)


@oauth2_required
@handle_errors
def display_object_revisions(request, client, obj_type, obj_ref, obj_revi):
    return pviews.display_object_revisions(request, obj_type,
            obj_ref, obj_revi)

