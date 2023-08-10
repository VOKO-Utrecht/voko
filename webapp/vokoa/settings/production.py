from .base import *

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'voko',
        'USER': 'voko',
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': 'localhost',
        }
    }

SERVER_EMAIL = "bestel@voedselkollektief.nl"

ADMINS = (
    ("Voedselkollektief", os.getenv('ADMIN_EMAIL', "ict@voedselkollektief.nl")),
)

ALLOWED_HOSTS = ("leden.voedselkollektief.nl", "acc.voedselkollektief.nl", "dev.voedselkollektief.nl", "127.0.0.1")

MOLLIE_API_KEY = os.environ["MOLLIE_API_KEY"]
