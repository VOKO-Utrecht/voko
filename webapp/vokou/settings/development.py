"""
Django settings for vokou project.

For more information on this file, see
https://docs.djangoproject.com/en/dev/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/dev/ref/settings/
"""

from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'da)=ydvhyj*u6%ldu_8hf%1op2efv!3q*%(ks=j19dvi$fu0oh'

DEBUG = True
ALLOWED_HOSTS = []

# Faster backend, useful while devving / testing
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'voko',
        'USER': 'voko',
        'PASSWORD': 'voko',
        'HOST': 'postgresql',
        }
    }

# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/app-messages'

INSTALLED_APPS += ['debug_toolbar',]
MIDDLEWARE_CLASSES = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE_CLASSES
INTERNAL_IPS = ['127.0.0.1']

CAPTCHA_ENABLED = False

try:
    from .local import *
except ImportError:
    pass
