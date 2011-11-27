import os
import sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'openPLM.settings'
os.environ["CELERY_LOADER"] = "django"

install_dir = '/var/demos/mobile_phone/'
sys.path.append(install_dir)
sys.path.append(install_dir + "openPLM/")

from openPLM.settings import INSTALLED_APPS
for app in INSTALLED_APPS:
    if app.startswith("openplm."):
        sys.path.append(install_dir + app.replace("openplm.", "openPLM/"))
import django.core.handlers.wsgi

application = django.core.handlers.wsgi.WSGIHandler()

