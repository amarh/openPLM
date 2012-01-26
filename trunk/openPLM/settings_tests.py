#-!- coding:utf-8 -!-
# Django settings for openPLM project.
# sqlite version

import sys
import os.path

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
    ("pcosquer", "pierre.cosquer@insa-rennes.fr"),
    ("pjoulaud", "ninoo.fr@gmail.com"),
)

MANAGERS = ADMINS

DATABASE_ENGINE = 'sqlite3'           # 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
DATABASE_NAME = 'database_tests.db'             # Or path to database file if using sqlite3.
DATABASE_USER = ''             # Not used with sqlite3.
DATABASE_PASSWORD = ''         # Not used with sqlite3.
DATABASE_HOST = ''             # Set to empty string for localhost. Not used with sqlite3.
DATABASE_PORT = ''             # Set to empty string for default. Not used with sqlite3.

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Paris'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en/en'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = 'media/'

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
    ('django.template.loaders.cached.Loader', (
    'django.template.loaders.filesystem.load_template_source',
    'django.template.loaders.app_directories.load_template_source',
    )),
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
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
    "templates",
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
    'openPLM.plmapp',
    # you can add your application after this line
    'openPLM.cad',
    'openPLM.computer',
    'openPLM.cae',
    'openPLM.office',
    'openPLM.gdoc',
    'openPLM.subversion',
    'openPLM.plmapp.tests',
)

AUTH_PROFILE_MODULE = 'plmapp.UserProfile'

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
######################
# openPLM's settings #
######################

#: directory that stores documents
DOCUMENTS_DIR = "/tmp/docs/"
THUMBNAILS_DIR = os.path.join(MEDIA_ROOT, "thumbnails")
#: directory that stores thumbnails
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
EMAIL_OPENPLM = "no-reply@openplm.example.com",

#: Max file size for documents in bytes, -1 means illimited
MAX_FILE_SIZE = -1

# search stuff
if "rebuild_index" not in sys.argv:
    HAYSTACK_ENABLE_REGISTRATIONS = False
HAYSTACK_SITECONF = 'openPLM.plmapp.search_sites'
HAYSTACK_SEARCH_ENGINE = 'xapian'
# use a memory backend
HAYSTACK_XAPIAN_PATH = ":memory:" 
# the memory backend does not support spelling
HAYSTACK_INCLUDE_SPELLING = False
EXTRACTOR = os.path.abspath("bin/extractor.sh")

# celery stuff
BROKER_BACKEND = "memory"
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

import djcelery
djcelery.setup_loader()

COMPANY = "company"

TEST_RUNNER = "openPLM.plmapp.tests.runner.OpenPLMTestSuiteRunner"
TEST_OUTPUT_DIR = "tests_results"

