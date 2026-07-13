import os

from .base import *  # noqa: F401, F403

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_NAME", os.environ.get("USER")),
        "USER": os.environ.get("POSTGRES_USER", os.environ.get("USER")),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", os.environ.get("DB_PASSWORD")),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": 5432,
    }
}

SERVER_EMAIL = "info@vokoutrecht.nl"
EMAIL_BACKEND = "django.core.mail.backends.filebased.EmailBackend"
EMAIL_FILE_PATH = "/tmp/app-messages"

ADMINS = (("Voko Utrecht", os.getenv("ADMIN_EMAIL", "info@vokoutrecht.nl")),)

ALLOWED_HOSTS = ("acc.leden.vokoutrecht.nl", "127.0.0.1")

CSRF_TRUSTED_ORIGINS = ["https://acc.leden.vokoutrecht.nl"]

BASE_URL = "http://acc.leden.vokoutrecht.nl"
MOLLIE_API_KEY = os.environ["MOLLIE_API_KEY"]
