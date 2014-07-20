from django.db import models
from vokou import settings


class Address(models.Model):
    city = models.CharField(max_length=255)


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    address = models.ForeignKey(Address)
