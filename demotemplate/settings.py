"""
Django settings for demotemplate project.

Generated by 'django-admin startproject' using Django 2.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/
"""

import os
import uuid
import dj_database_url
from env_tools import apply_env

apply_env()

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY', 'yoursecretkeyhere')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False if os.getenv('DEBUG', '').lower() == 'false' else True

REMOTE = True if os.getenv('REMOTE', '').lower() == 'true' else False
if REMOTE:
    SECURE_SSL_REDIRECT = True

ALLOWED_HOSTS = ['*']

HEROKUCONFIG_APP_NAME = os.getenv('HEROKUCONFIG_APP_NAME', '')

DEFAULT_BASE_URL = ('http://localhost:5000')

OPENHUMANS_APP_BASE_URL = os.getenv('APP_BASE_URL', DEFAULT_BASE_URL)
if OPENHUMANS_APP_BASE_URL[-1] == "/":
    OPENHUMANS_APP_BASE_URL = OPENHUMANS_APP_BASE_URL[:-1]

# OAuth configuration
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
# for microsoft oauth2
AUTHORITY_HOST_URL = os.getenv('AUTHORITY_HOST_URL') + '/' + os.getenv('TENANT')
OAUTH2_RESOURCE = os.getenv('OAUTH2_RESOURCE') # for token access
OAUTH2_SCOPES = ['offline_access', 'User.Read'] # Add other scopes/permissions as needed.
REDIRECT_URI = os.getenv('REDIRECT_URI')
AUTH_STATE = str(uuid.uuid4())

### TBD: needed for now, but we the INSECURE_TRANSPORT can be eliminated once out of dev
# Enable non-HTTPS redirect URI for development/testing.
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
# Allow token scope to not match requested scope. (Other auth libraries allow
# this, but Requests-OAuthlib raises exception on scope mismatch by default.)
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
os.environ['OAUTHLIB_IGNORE_SCOPE_CHANGE'] = '1'

OH_ACTIVITY_PAGE = os.getenv('OH_ACTIVITY_PAGE')

OH_BASE_URL = 'https://www.openhumans.org'

OH_API_BASE = OH_BASE_URL + '/api/direct-sharing'
OH_DIRECT_UPLOAD = OH_API_BASE + '/project/files/upload/direct/'
OH_DIRECT_UPLOAD_COMPLETE = OH_API_BASE + '/project/files/upload/complete/'
OH_DELETE_FILES = OH_API_BASE + '/project/files/delete/'

JUPYTERHUB_BASE_URL = os.getenv('JUPYTERHUB_BASE_URL',
                                'http://localhost:8888')

# Applications installed
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Local apps. Update these if you add or change app names!
    'open_humans.apps.OpenHumansConfig',
    'main.apps.MainConfig'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

MIDDLEWARE_CLASSES = [
    # Simplified static file serving.
    # https://warehouse.python.org/project/whitenoise/
    'whitenoise.middleware.WhiteNoiseMiddleware'
]

ROOT_URLCONF = 'demotemplate.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'demotemplate.context_processors.login_fills'
            ],
        },
    },
]

WSGI_APPLICATION = 'demotemplate.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases
# https://devcenter.heroku.com/articles/django-app-configuration


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

db_from_env = dj_database_url.config(conn_max_age=500)
DATABASES['default'].update(db_from_env)


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': ('django.contrib.auth.password_validation.'
                 'UserAttributeSimilarityValidator'),
    },
    {
        'NAME': ('django.contrib.auth.password_validation.'
                 'MinimumLengthValidator'),
    },
    {
        'NAME': ('django.contrib.auth.password_validation.'
                 'CommonPasswordValidator'),
    },
    {
        'NAME': ('django.contrib.auth.password_validation.'
                 'NumericPasswordValidator'),
    },
]

# Configure logging to print Django logs to the console.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
        },
    },
}


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Simplified static file serving.
# https://warehouse.python.org/project/whitenoise/

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
