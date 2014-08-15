from uuid import uuid4
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ObjectDoesNotExist
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

    def save(self, *args, **kwargs):
        if self.is_active and not self.email_confirmation.is_confirmed:
            raise RuntimeError("Email address is not confirmed!")

        super(VokoUser, self).save(*args, **kwargs)

        try:
            _ = self.email_confirmation
        except ObjectDoesNotExist:
            EmailConfirmation.objects.create(user=self)


class EmailConfirmation(models.Model):
    token = models.CharField(max_length=100, primary_key=True)
    # OneToOneField might be impractical when user changes his e-mail address. (TODO?)
    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="email_confirmation")
    is_confirmed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = str(uuid4())
        super(EmailConfirmation, self).save(*args, **kwargs)

    def confirm(self):
        self.is_confirmed = True
        self.save()

    def __unicode__(self):
        return "Confirmed: %s | user: %s | email: %s" % (self.is_confirmed, self.user, self.user.email)
