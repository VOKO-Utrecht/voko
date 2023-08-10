from .base import *

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['USER'],
        'USER': os.environ['USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': 'localhost',
        }
    }

SERVER_EMAIL = "ict@voedselkollektief.nl"
EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp/app-messages'

ADMINS = (
    ("Voedselkollektief", os.getenv('ADMIN_EMAIL', "ict@voedselkollektief.nl")),
)

ALLOWED_HOSTS = ("acc.leden.voedselkollektief.nl", "127.0.0.1")

BASE_URL = "http://acc.leden.voedselkollektief.nl"
MOLLIE_API_KEY = os.environ["MOLLIE_API_KEY"]
