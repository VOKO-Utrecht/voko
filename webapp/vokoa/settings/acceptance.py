from .base import *

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['POSTGRES_DB'],
        'USER': os.environ['POSTGRES_USER'],
        'PASSWORD': os.environ['POSTGRES_PASSWORD'],
        'HOST': os.environ['POSTGRES_HOST'],
        }
    }

SERVER_EMAIL = "ict@voedselkollektief.nl"
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/app-messages'

ADMINS = (
    ("Voedselkollektief", os.getenv('ADMIN_EMAIL', "ict@voedselkollektief.nl")),
)

ALLOWED_HOSTS = ("leden.acc.voedselkollektief.nl", "127.0.0.1", "localhost")

# BASE_URL = os.environ["VIRTUAL_HOST"]
MOLLIE_API_KEY = os.environ["MOLLIE_API_KEY"]

# RECAPTCHA Config
RECAPTCHA_PUBLIC_KEY = os.environ["RECAPTCHA_PUBLIC_KEY"]
RECAPTCHA_PRIVATE_KEY = os.environ["RECAPTCHA_PRIVATE_KEY"]
