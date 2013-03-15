import datetime
from django.utils import timezone
import urlparse

import pysvn

from openPLM.plmapp.utils import r2r
from openPLM.plmapp.views.base import handle_errors, get_generic_data

from openPLM.apps.subversion.models import parse_revision


@handle_errors
def display_files(request, obj_type, obj_ref, obj_revi):
    """
    Files page of a SubversionRepository.
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    ctx['current_page'] = 'files'
    return r2r('subversion_files.html', ctx, request)

def get_day(log):
    date = log["date"]
    return datetime.date(date.year, date.month, date.day)

@handle_errors
def logs(request, obj_type, obj_ref, obj_revi):
    """
    Logs page of a SubversionRepository.
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)
    ctx['current_page'] = 'logs'
    return r2r('logs.html', ctx, request)


@handle_errors
def ajax_logs(request, obj_type, obj_ref, obj_revi):
    """
    Ajax Logs page of a SubversionRepository.
    """
    obj, ctx = get_generic_data(request, obj_type, obj_ref, obj_revi)

    ctx["error"] = False
    try:
        revision = parse_revision(obj.svn_revision)
        uri = obj.repository_uri
        if uri.startswith("file://") or uri.startswith("/"):
            raise ValueError()
        client = pysvn.Client()
        if not client.is_url(uri):
            raise ValueError()
        # parse uri and set credentials if given
        parts = urlparse.urlparse(uri)
        if parts.username and parts.password:
            client.callback_get_login = lambda *args: (True, parts.username,
                    parts.password, True)
        logs = client.log(uri, limit=20, revision_start=revision)
        for log in logs:
            log["date"] = datetime.datetime.fromtimestamp(log["date"])
            log["day"] = get_day(log)
        ctx["logs"] = logs
    except (ValueError, pysvn.ClientError):
        ctx["error"] = True

    ctx['current_page'] = 'logs'
    return r2r('ajax_logs.html', ctx, request)


