from .development import *

# Faster backend, useful while devving / testing
PASSWORD_HASHERS = (
    'django.contrib.auth.hashers.MD5PasswordHasher',
)

DEBUG = False
TEMPLATE_DEBUG = DEBUG


# https://stackoverflow.com/questions/25161425/disable-migrations-when-running-unit-tests-in-django-1-7 
class DisableMigrations(object):
    def __contains__(self, item):
        return True
 
    def __getitem__(self, item):
        return "notmigrations"
 
MIGRATION_MODULES = DisableMigrations()
