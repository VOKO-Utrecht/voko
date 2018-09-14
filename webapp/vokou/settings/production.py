from .base import *

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'voko',
        'USER': 'voko',
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': 'localhost',
        }
    }

DEFAULT_FROM_EMAIL = "VOKO Utrecht <info@vokoutrecht.nl>"
SERVER_EMAIL = "info@vokoutrecht.nl"

ADMINS = (
    ("Voko Utrecht", os.getenv('ADMIN_EMAIL', "info@vokoutrecht.nl")),
)

ALLOWED_HOSTS = ("leden.vokoutrecht.nl", "dev.vokoutrecht.nl", "127.0.0.1")

MOLLIE_API_KEY = os.environ["MOLLIE_API_KEY"]
