import os.path
import sys

DEBUG = False
TEMPLATE_DEBUG = DEBUG

QA_SERVER = False  # triggers minor UI changes

PROJECT_DIR = os.path.abspath(
                      os.path.join(os.path.dirname(__file__), '..', '..'))

ABSDIR = lambda path: os.path.abspath(os.path.join(PROJECT_DIR, path))

ADMINS = (
    ('Udi Oron', 'udioron@gmail.com'),
)

EMAIL_SUBJECT_PREFIX = '[OpenCommunity] '
FROM_EMAIL = "noreply@opencommunity.dev"
HOST_URL = "http://localhost:8000"

MANAGERS = (('Boaz Chen', 'boaz.chen@gmail.com'),)

DATABASES = {
    'default': {
        # engines: '.postgresql_psycopg2', '.mysql', '.sqlite3' or '.oracle'.
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'opencommunity',
        'USER': 'postgres',
        'PASSWORD': 'peta2drs',
        'HOST': 'localhost',
        'PORT': '',
    }
}

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = []

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'Asia/Jerusalem'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'he'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

if 'test' in sys.argv:
    DATABASES['default'] = {'ENGINE': 'django.db.backends.sqlite3'}
    TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
    LANGUAGE_CODE ='en'
LOCALE_PATHS = (
    ABSDIR('src/ocd/locale'),
)

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = True

UPLOAD_PATH = ABSDIR('uploads')

UPLOAD_ALLOWED_EXTS = [
                       'pdf', 'txt', 'doc', 'docx', 'xls', 'xlsx', 'csv',
                       'jpg', 'jpeg', 'gif', 'png', 'tiff', 'ppt', 'pptx',
                       'rtf', 'mp3', 'wav', 'flac', 'm4a', 'wma', 'aac',
                       'fla', 'mp4', 'mov', 'avi', 'wmv',
                      ]

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = ABSDIR('media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = ABSDIR('static')

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.abspath(os.path.join(os.path.dirname(__file__), "static")),
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '!9cmmoa+#@=9o33n+wf+kf)))u6!0b)z(l-h-sq4sk*jv9&^6*'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # Uncomment the next line for simple clickjacking protection:
    # 'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'ocd.urls'

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'ocd.wsgi.application'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.abspath(os.path.join(os.path.dirname(__file__), "templates")),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    #'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.humanize',

    'floppyforms',
    'south',
    'django_nose',
    'django_extensions',
    'debug_toolbar',
    'taggit',
    'haystack',
    'oc_util',
    'users',
    'communities',
    'issues',
    'meetings',
    'shultze',

)


AUTH_USER_MODEL = 'users.OCUser'


HAYSTACK_CONNECTIONS = {
    'default': {
        'ENGINE': 'ocd.custom_whoosh_backend.MyWhooshEngine',
        'PATH': os.path.join(PROJECT_DIR, 'whoosh_index'),
    },
}

HAYSTACK_CUSTOM_HIGHLIGHTER = 'ocd.custom_highlighting.MyHighlighter'
HAYSTACK_SIGNAL_PROCESSOR = 'haystack.signals.RealtimeSignalProcessor'

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse'
        }
    },
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
     },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}

LOGIN_REDIRECT_URL = "/"
LOGIN_URL = "/login/"
LOGOUT_URL = "/logout/"

FORMAT_MODULE_PATH = "ocd.formats"
DATE_FORMAT_OCSHORTDATE = "j.n"
DATE_FORMAT_OCSHORTTIME = "H:i"
# DATETIME_FORMAT = '%d/%m/%Y %H:%M'

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.core.context_processors.tz',
    'django.core.context_processors.request',
    'django.contrib.messages.context_processors.messages',
    'ocd.context_processors.analytics',
    'ocd.context_processors.smart_404',
)

SESSION_REMEMBER_DAYS = 45
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Made accessible to templates via the analytics context processor `analytics`
OPENCOMMUNITY_ANALYTICS = {
    'piwik': {
        'host': 'visitors.hasadna.org.il/',
        'id': '3'
    },
    # Uncomment & configure for Google Analytics tracking
    # 'ga': {
    #     'id': 'UA-00000000-0'
    #     'url': 'domain.com'
    # }
}

version_file = os.path.join(STATIC_ROOT, 'version.txt')
if os.path.exists(version_file):
    with open(version_file) as f:
        OPENCOMMUNITY_VERSION = f.read()
else:
    OPENCOMMUNITY_VERSION = None

try:
    from local_settings import *
except ImportError:
    pass
