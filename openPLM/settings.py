#-!- coding:utf-8 -!-
# Django settings for openPLM project.
# sqlite version

import sys
import os.path

DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'postgresql_psycopg2'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'openplm'             # Or path to database file if using sqlite3.
DATABASE_USER = 'django'             # Not used with sqlite3.
DATABASE_PASSWORD = 'django#6'         # Not used with sqlite3.
DATABASE_HOST = 'localhost'             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Paris'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-en'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = '/var/django/openPLM/trunk/openPLM/media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = '/media/admin/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '0ham7d#fh669-xi@wxf1wcpbhn6tbbegtv_cml()_wcboyw&u&'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.csrf.middleware.CsrfMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
)

ugettext = lambda s: s
LANGUAGES = (
      ('fr', u'Français'),
      ('en', 'English'),
      ('es', u'Español'),
)

ROOT_URLCONF = 'openPLM.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    "/var/django/openPLM/trunk/openPLM/templates",
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.comments',
    'django.contrib.humanize',
    'djcelery',
    'haystack',
    'south',
    'openPLM.plmapp',
    # you can add your application after this line
    'openPLM.cad',
    'openPLM.computer',
    'openPLM.cae',
    'openPLM.office',
)

AUTH_PROFILE_MODULE = 'plmapp.UserProfile'

CELERY_CREATE_MISSING_QUEUES = True
CELERY_ROUTES = {
    "openPLM.plmapp.tasks.update_index": {"queue": "index"},
    "openPLM.plmapp.tasks.update_indexes": {"queue": "index"},
    "openPLM.plmapp.mail.do_send_histories_mail" : {"queue" : "mails"},
    "openPLM.plmapp.mail.do_send_mail" : {"queue" : "mails"},
}

EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025

######################
# openPLM's settings #
######################

#: directory that stores documents. Make sure to use a trailing slash.
DOCUMENTS_DIR = "/var/openPLM/docs/"
THUMBNAILS_DIR = os.path.join(MEDIA_ROOT, "thumbnails/")
#: directory that stores thumbnails. Make sure to use a trailing slash.
THUMBNAILS_URL = MEDIA_URL + "thumbnails/"

# Cookie used for session is temporary and is deleted when browser is closed
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Add user, messages and perms variables in RequestContext
TEMPLATE_CONTEXT_PROCESSORS = (
        "django.contrib.auth.context_processors.auth",
        "django.core.context_processors.debug",
        "django.core.context_processors.i18n",
        "django.core.context_processors.media",
        "django.core.context_processors.request",
        )



#: expeditor's mail used when sending notification emails
EMAIL_OPENPLM = "no-reply@openplm.example.com"

#: Max file size for documents in bytes, -1 means illimited
MAX_FILE_SIZE = -1

# search stuff
if "rebuild_index" not in sys.argv:
    HAYSTACK_ENABLE_REGISTRATIONS = False
HAYSTACK_SITECONF = 'openPLM.plmapp.search_sites'
HAYSTACK_SEARCH_ENGINE = 'xapian'
HAYSTACK_XAPIAN_PATH = "/var/openPLM/xapian_index/"
HAYSTACK_INCLUDE_SPELLING = True
EXTRACTOR = os.path.abspath(os.path.join(os.path.dirname(__file__), "bin", "extractor.sh"))

# celery stuff
import djcelery
djcelery.setup_loader()

BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = "openplm"
BROKER_PASSWORD = "secret"
BROKER_VHOST = "openplm"

# change these settings to True to force https connection 
#: set to True so that browsers ensure the cookie is only sent under an HTTPS connection
SESSION_COOKIE_SECURE = False
#: Force HTTPS connections
FORCE_HTTPS = False

COMPANY = "company"

