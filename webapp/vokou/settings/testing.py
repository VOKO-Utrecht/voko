from .development import *

# Faster backend, useful while devving / testing
PASSWORD_HASHERS = ("django.contrib.auth.hashers.MD5PasswordHasher",)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "db.sqlite3"),
    }
}

DEBUG = False
