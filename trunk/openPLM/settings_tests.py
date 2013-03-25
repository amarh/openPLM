#-!- coding:utf-8 -!-

import warnings
warnings.filterwarnings(
        'error', r"DateTimeField received a naive datetime",
        RuntimeWarning, r'django\.db\.models\.fields')

# Django settings for openPLM project.
# tests version

import sys
import os.path

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', # or 'postgresql', 'mysql', 'sqlite3', 'oracle'.
        'NAME': 'database_tests.db',               # Or path to database file if using sqlite3.
    }
}


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

STATIC_ROOT = os.path.join(PROJECT_ROOT, "static")
STATIC_URL = "/static/"

# Make this unique, and don't share it with anybody.
SECRET_KEY = '0ham7d#fh669-xi@wxf1wcpbhn6tbbegtv_cml()_wcboyw&u&'

# Set faster password hashers for tests
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)
# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
    "django.template.loaders.filesystem.Loader",
    "django.template.loaders.app_directories.Loader",
    )),
#     'django.template.loaders.eggs.load_template_source',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'openPLM.plmapp.middleware.locale.ProfileLocaleMiddleware',
    'openPLM.apps.badges.middleware.GlobalRequest',

)
LOCALE_PATHS = (
    os.path.join(PROJECT_ROOT, "locale"),
)

ugettext = lambda s: s
LANGUAGES = (
      ('fr', u'Français'),
      ('en', 'English'),
      ('es', u'Español'),
      ('ja', u'日本語'),
      ('ru', u'Русский'),
      ('zh_CN', u'中文'),
)

ROOT_URLCONF = 'openPLM.urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    "templates",
)
USE_TZ = True

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.admin',
    'django.contrib.comments',
    'django.contrib.humanize',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'djcelery',
    'haystack',
    'openPLM.plmapp',
    'openPLM.apps.rss',
    'openPLM.apps.pdfgen',
    'openPLM.apps.calendrier',
    # you can add your application after this line
    'openPLM.apps.cad',
    'openPLM.apps.computer',
    'openPLM.apps.cae',
    'openPLM.apps.office',
    'openPLM.apps.gdoc',
    'openPLM.apps.subversion',
    'openPLM.apps.ecr',
    'openPLM.apps.badges',
    'openPLM.apps.richpage',
    'openPLM.plmapp.tests',
)

if os.environ.get("openPLM3D", "") == "enabled":
    INSTALLED_APPS += ("openPLM.apps.document3D", )

COMMENTS_APP = "openPLM.plmapp"
RICHTEXT_FILTER = 'openPLM.plmapp.filters.markdown_filter'
RICHTEXT_WIDGET_CLASS = 'openPLM.plmapp.widgets.MarkdownWidget'

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
MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

# Add user, messages and perms variables in RequestContext
TEMPLATE_CONTEXT_PROCESSORS = (
        "django.contrib.auth.context_processors.auth",
        "django.core.context_processors.debug",
        "django.core.context_processors.i18n",
        "django.core.context_processors.media",
        "django.core.context_processors.static",
        "django.core.context_processors.request",
        "django.contrib.messages.context_processors.messages",
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
# use a memory backend
HAYSTACK_XAPIAN_PATH = ":memory:"
# the memory backend does not support spelling
HAYSTACK_INCLUDE_SPELLING = False
EXTRACTOR = os.path.abspath("bin/extractor.sh")

# celery stuff
BROKER_BACKEND = "memory"
CELERY_ALWAYS_EAGER = True
CELERY_EAGER_PROPAGATES_EXCEPTIONS = True

#Gestion native
ENABLE_NATIVE_FILE_MANAGEMENT=True


import djcelery
djcelery.setup_loader()

COMPANY = "company"

HIDE_EMAILS = False

TEST_RUNNER = "openPLM.plmapp.tests.runner.OpenPLMTestSuiteRunner"
TEST_OUTPUT_DIR = "tests_results"

DOCUMENTATION_URL ="http://wiki.openplm.org/docs/user/"
