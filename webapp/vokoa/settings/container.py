from .base import *
from distutils.util import strtobool

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

# Production mode
DEBUG = os.getenv("DJANGO_ENV") != "production"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['POSTGRES_DB'],
        'USER': os.environ['POSTGRES_USER'],
        'PASSWORD': os.environ['POSTGRES_PASSWORD'],
        'HOST': os.environ['POSTGRES_HOST'],
        }
    }

DEFAULT_FROM_EMAIL = os.environ["DEFAULT_FROM_EMAIL"]
SERVER_EMAIL = os.environ['SERVER_EMAIL']
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ['EMAIL_HOST']
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = strtobool(os.getenv("EMAIL_USE_TLS", "True"))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

ADMINS = (
    ("Voedselkollektief", os.getenv('ADMIN_EMAIL', "ict@voedselkollektief.nl")),
)

BASE_URL = os.environ["BASE_URL"]
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS').split(",")

# BASE_URL = os.environ["VIRTUAL_HOST"]
MOLLIE_API_KEY = os.environ["MOLLIE_API_KEY"]

# RECAPTCHA Config
RECAPTCHA_PUBLIC_KEY = os.environ["RECAPTCHA_PUBLIC_KEY"]
RECAPTCHA_PRIVATE_KEY = os.environ["RECAPTCHA_PRIVATE_KEY"]
