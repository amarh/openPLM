import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'openPLM.settings'
os.environ["CELERY_LOADER"] = "django"

sys.path.append('/var/django/openPLM/trunk/')
sys.path.append('/var/django/openPLM/trunk/openPLM')

from django import db
from django.conf import settings
from django.contrib.sessions.backends.db import SessionStore
from django.contrib.auth.models import User
from django.core.handlers.wsgi import WSGIRequest
from django.contrib.sessions.middleware import SessionMiddleware

def allow_access(environ, host):
    """
    Authentication handler that checks if user is logged in
    and not restricted.
    """

    from django.contrib.auth import get_user
    # Fake this, allow_access gets a stripped environ
    environ['wsgi.input'] = None

    request = WSGIRequest(environ)
    SessionMiddleware().process_request(request)
    errors = environ['wsgi.errors']
    allowed = False
    try:
        user = get_user(request)
        if user.is_authenticated():
            allowed = not user.profile.restricted
    except Exception as e:
        errors.write('Exception: %s\n' % e)
    finally:
        db.connection.close()
    return allowed


