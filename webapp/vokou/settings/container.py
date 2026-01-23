import os

from .base import *  # noqa: F401, F403


def strtobool(val):
    val = val.lower()
    if val in ("y", "yes", "t", "true", "on", "1"):
        return True
    elif val in ("n", "no", "f", "false", "off", "0"):
        return False
    else:
        raise ValueError(f"invalid truth value {val!r}")


SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

DEBUG = os.environ.get("DJANGO_DEBUG", "false").lower() in ("true", "1", "yes")

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_NAME", "postgres"),
        "USER": os.environ["POSTGRES_USER"],
        "PASSWORD": os.environ["POSTGRES_PASSWORD"],
        "HOST": os.environ["POSTGRES_HOST"],
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", DEFAULT_FROM_EMAIL)
SERVER_EMAIL = os.environ.get("SERVER_EMAIL", ORGANIZATION_EMAIL)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.environ.get("EMAIL_HOST", "localhost")
EMAIL_PORT = int(os.environ.get("EMAIL_PORT", "587"))
EMAIL_USE_TLS = strtobool(os.environ.get("EMAIL_USE_TLS", "True"))
EMAIL_HOST_USER = os.environ.get("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.environ.get("EMAIL_HOST_PASSWORD", "")

ADMINS = [
    (ORGANIZATION_NAME, os.environ.get("ADMIN_EMAIL", ORGANIZATION_EMAIL)),
]

BASE_URL = os.environ.get("BASE_URL", BASE_URL)
_raw_allowed_hosts = os.environ.get("ALLOWED_HOSTS", "")
ALLOWED_HOSTS = [h.strip() for h in _raw_allowed_hosts.split(",") if h.strip()]

MOLLIE_API_KEY = os.environ.get("MOLLIE_API_KEY", "SETME")

RECAPTCHA_PUBLIC_KEY = os.environ.get("RECAPTCHA_PUBLIC_KEY", "")
RECAPTCHA_PRIVATE_KEY = os.environ.get("RECAPTCHA_PRIVATE_KEY", "")
