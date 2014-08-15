from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.db import models
from vokou import settings
from django.utils.translation import ugettext_lazy as _


class Address(models.Model):
    street_and_number = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=7)
    city = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        return "%s - %s, %s" % (self.street_and_number, self.zip_code, self.city)


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL)
    address = models.ForeignKey(Address)


class VokoUserManager(BaseUserManager):
    def create_user(self, email, first_name, last_name, password=None):
        if not email:
            msg = "Users must have an email address"
            raise ValueError(msg)
        user = self.model(email=VokoUserManager.normalize_email(email),
                          first_name=first_name,
                          last_name=last_name)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, first_name, last_name, password):
        user = self.create_user(email, first_name, last_name, password=password)
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class VokoUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        verbose_name="email address",
        max_length=255,
        unique=True,
        db_index=True,
    )

    first_name = models.CharField(_('first name'), max_length=30)
    last_name = models.CharField(_('last name'), max_length=30)

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = ["first_name", "last_name"]
    is_active = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    objects = VokoUserManager()

    def get_full_name(self):
        return "%s %s" % (self.first_name, self.last_name)

    def get_short_name(self):
        return self.email

    def __unicode__(self):
        return self.get_full_name()
