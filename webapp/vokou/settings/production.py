import os

from .base import *  # noqa: F401, F403

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_NAME", "voko"),
        "USER": os.environ.get("POSTGRES_USER", "voko"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", os.environ.get("DB_PASSWORD")),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": 5432,
    }
}

SERVER_EMAIL = "info@vokoutrecht.nl"

ADMINS = (("Voko Utrecht", os.getenv("ADMIN_EMAIL", "info@vokoutrecht.nl")),)

ALLOWED_HOSTS = ("ldn.vokoutrecht.nl", "leden.vokoutrecht.nl", "acc.vokoutrecht.nl", "dev.vokoutrecht.nl", "127.0.0.1")

CSRF_TRUSTED_ORIGINS = ["https://leden.vokoutrecht.nl"]

MOLLIE_API_KEY = os.environ["MOLLIE_API_KEY"]
