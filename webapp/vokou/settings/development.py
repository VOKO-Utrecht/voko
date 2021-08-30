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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}

# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/app-messages'

INSTALLED_APPS += ['debug_toolbar',]
MIDDLEWARE_CLASSES = ['debug_toolbar.middleware.DebugToolbarMiddleware'] + MIDDLEWARE_CLASSES
INTERNAL_IPS = ['127.0.0.1']

NOCAPTCHA = True
CAPTCHA_ENABLED = True

RECAPTCHA_PRIVATE_KEY='6LeIxAcTAAAAAGG-vFI1TnRWxMZNFuojJ4WifJWe'
RECAPTCHA_PUBLIC_KEY='6LeIxAcTAAAAAJcZVRqyHh71UMIEGNQ_MXjiZKhI'
SILENCED_SYSTEM_CHECKS = ['captcha.recaptcha_test_key_error']

# MOLLIE_API_KEY = 'test_'

try:
    from .local import *
except ImportError:
    pass
