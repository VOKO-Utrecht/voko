from .base import *

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ['USER'],
        'USER': os.environ['USER'],
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': 'localhost',
        }
    }

SERVER_EMAIL = "info@vokoutrecht.nl"

ADMINS = (
    ("Voko Utrecht", os.getenv('ADMIN_EMAIL', "info@vokoutrecht.nl")),
)

ALLOWED_HOSTS = ("acc.leden.vokoutrecht.nl")

MOLLIE_API_KEY = os.environ["MOLLIE_API_KEY"]
