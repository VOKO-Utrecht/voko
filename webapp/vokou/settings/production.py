from .base import *

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'vokou',                      # Or path to database file if using sqlite3.
        'USER': 'vokou',
        'PASSWORD': os.environ['DB_PASSWORD'],
        'HOST': 'localhost',                      # Empty for localhost through domain sockets or           '127.0.0.1' for localhost through TCP.
        }
    }

DEFAULT_FROM_EMAIL = "VOKO Utrecht <info@vokoutrecht.nl>"
SERVER_EMAIL = "info@vokoutrecht.nl"

ADMINS = (
    ("Voko Utrecht", "info@vokoutrecht.nl"),
)
ALLOWED_HOSTS = ("leden.vokoutrecht.nl",)

MOLLIE_API_KEY = os.environ["MOLLIE_API_KEY"]

INSTALLED_APPS += (
    "opbeat.contrib.django",
)

OPBEAT = {
    "ORGANIZATION_ID": os.environ["OPBEAT_ORGANIZATION_ID"],
    "APP_ID": os.environ["OPBEAT_APP_ID"],
    "SECRET_TOKEN": os.environ["OPBEAT_SECRET"]
}

MIDDLEWARE_CLASSES = (
    'opbeat.contrib.django.middleware.OpbeatAPMMiddleware',
) + MIDDLEWARE_CLASSES
