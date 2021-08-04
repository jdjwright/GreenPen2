"""
Django settings for GreenPen project.

Generated by 'django-admin startproject' using Django 3.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os, datetime


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DJANGO_DEBUG') == 'True'

ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS').split()


# Application definition

INSTALLED_APPS = [
    'dal_select2',
    'dal',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'debug_toolbar',
    'GreenPen',
    'mptt',
    'crispy_forms',
    'django_plotly_dash.apps.DjangoPlotlyDashConfig',
    'channels',
    'social_django',
    'jstree',
    'ckeditor',
    'ckeditor_uploader',
    'django_extensions'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
   # 'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django_plotly_dash.middleware.BaseMiddleware',
]

CRISPY_TEMPLATE_PACK = 'bootstrap4'

ROOT_URLCONF = 'GreenPen.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'social_django.context_processors.backends',
                'social_django.context_processors.login_redirect',
            ],
        },
    },
]

WSGI_APPLICATION = 'GreenPen.wsgi.application'

ASGI_APPLICATION = 'GreenPen.routing.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379),],
        }
    }
}

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django_plotly_dash.finders.DashAssetFinder',
    'django_plotly_dash.finders.DashComponentFinder'
]

PLOTLY_COMPONENTS = [
    'dash_core_components',
    'dash_html_components',
    'dash_renderer',
    'dash_bootstrap_components',
    'dpd_components'
]
# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#     }
# }

DATABASES = {
    "default": {
        "ENGINE": os.environ.get("SQL_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("SQL_DATABASE", os.path.join(BASE_DIR, "db.sqlite3")),
        "USER": os.environ.get("SQL_USER", "user"),
        "PASSWORD": os.environ.get("SQL_PASSWORD", "password"),
        "HOST": os.environ.get("SQL_HOST", "localhost"),
        "PORT": os.environ.get("SQL_PORT", "5432"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# For Django Debug Toolbar:

INTERNAL_IPS = [
    # ...
    '127.0.0.1',
    '172.19.0.1',
]

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/staticfiles/'
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")

MEDIA_URL = "/mediafiles/"
MEDIA_ROOT = os.path.join(BASE_DIR, "mediafiles")

X_FRAME_OPTIONS = 'SAMEORIGIN'


# ACADEMIC YEAR SETUP

# These lists should be for each academic year, in the following format:

# [2018-19, 2019-20, 2020-2021, etc...]

CALENDAR_START_MONDAY_DAY = [20, 19, 14]
CALENDAR_START_MONTH = [8, 8, 8]
CALENDAR_START_YEAR = [2018, 2019, 2020]

CALENDAR_END_DAY = [29, 1, 26]
CALENDAR_END_MONTH = [6, 7, 6]
CALENDAR_END_YEAR = [2019, 2020, 2021]



ACADEMIC_YEARS = {0: "2018-19",
                  1: "2019-20",
                  2: "2020-21"}

# AUTOMATIC academic year setup - do not edit.

CALENDAR_START_DATE = []
CALENDAR_END_DATE = []

CURRENT_ACADEMIC_YEAR = 2
PRINTABLE_CUR_A_YEAR = ACADEMIC_YEARS[CURRENT_ACADEMIC_YEAR]

n = 0
for day in CALENDAR_END_DAY:

    CALENDAR_START_DATE.append(datetime.date(CALENDAR_START_YEAR[n], CALENDAR_START_MONTH[n], CALENDAR_START_MONDAY_DAY[n]))

    CALENDAR_END_DATE.append(datetime.date(CALENDAR_END_YEAR[n], CALENDAR_END_MONTH[n], CALENDAR_END_DAY[n]))
    n = n+1

CALENDAR_TOTAL_WEEKS = []
n = 0
for day in CALENDAR_START_DATE:
    monday1 = (CALENDAR_START_DATE[n] - datetime.timedelta(days=CALENDAR_START_DATE[n].weekday()))
    monday2 = (CALENDAR_END_DATE[n] - datetime.timedelta(days=CALENDAR_END_DATE[n].weekday()))
    CALENDAR_TOTAL_WEEKS.append((monday2 - monday1).days / 7)


# Required for django social-auth
SOCIAL_AUTH_POSTGRES_JSONFIELD = True

AUTHENTICATION_BACKENDS = (
    'social_core.backends.google.GoogleOAuth2',  # for Google authentication

    'django.contrib.auth.backends.ModelBackend',
)

SOCIAL_AUTH_PIPELINE = (
    'social_core.pipeline.social_auth.social_details',
    'social_core.pipeline.social_auth.social_uid',
    'social_core.pipeline.social_auth.auth_allowed',
    'social_core.pipeline.social_auth.social_user',
    'social_core.pipeline.social_auth.associate_by_email',
    'social_core.pipeline.social_auth.associate_user',
    'social_core.pipeline.social_auth.load_extra_data',
    'social_core.pipeline.user.user_details',
)

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY=os.getenv('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET=os.getenv('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET')

LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/login'

# For creating Jupyter notebooks:
SHELL_PLUS = "ipython"

SHELL_PLUS_PRINT_SQL = True

NOTEBOOK_ARGUMENTS = [
    "--ip",
    "0.0.0.0",
    "--port",
    "8888",
    "--allow-root",
    "--no-browser",
]

IPYTHON_ARGUMENTS = [
    "--ext",
    "django_extensions.management.notebook_extension",
    "--debug",
]

IPYTHON_KERNEL_DISPLAY_NAME = "Django Shell-Plus"

if DEBUG:
    os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true" # only use in development


CKEDITOR_UPLOAD_PATH = MEDIA_ROOT
CKEDITOR_ALLOW_NONIMAGE_FILES = False

# Boostrap messages settings (see https://simpleisbetterthancomplex.com/tips/2016/09/06/django-tip-14-messages-framework.html)
from django.contrib.messages import constants as messages

MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

DATA_UPLOAD_MAX_NUMBER_FIELDS = None
