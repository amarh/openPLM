import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'openPLM.settings'
os.environ["CELERY_LOADER"] = "django"

sys.path.append('/var/django/openPLM/trunk/')
sys.path.append('/var/django/openPLM/trunk/openPLM')

from openPLM.settings import INSTALLED_APPS
for app in INSTALLED_APPS:
    if app.startswith("openplm."):
        sys.path.append('/var/django/openPLM/trunk/%s' % app.replace("openplm.", "openPLM/"))
import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()

