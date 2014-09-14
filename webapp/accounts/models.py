from uuid import uuid4
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db import models
from django_extensions.db.models import TimeStampedModel
from accounts.mails import email_confirm_mail
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


class Address(TimeStampedModel):
    class Meta:
        verbose_name = "adres"
        verbose_name_plural = "adressen"

    street_and_number = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=7)
    city = models.CharField(max_length=100, blank=True)

    def __unicode__(self):
        return "%s - %s, %s" % (self.street_and_number, self.zip_code, self.city)


class UserProfile(TimeStampedModel):
    class Meta:
        verbose_name = "ledenprofiel"
        verbose_name_plural = "ledenprofielen"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, related_name="userprofile")
    address = models.ForeignKey(Address)
    notes = models.TextField()
    
    def __unicode__(self):
        return "Profile for user: %s" % self.user


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
        user.is_active = True
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.save(using=self._db)
        return user


class VokoUser(TimeStampedModel, AbstractBaseUser, PermissionsMixin):
    class Meta:
        verbose_name = "lid"
        verbose_name_plural = "leden"

    email = models.EmailField(
        verbose_name="E-mail adres",
        max_length=255,
        unique=True,
        db_index=True,
    )

    first_name = models.CharField(_('Voornaam'), max_length=30)
    last_name = models.CharField(_('Achternaam'), max_length=30)

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = ["first_name", "last_name"]
    can_activate = models.BooleanField(default=False)
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
        # Disabled because this breaks admin login (TODO)
        # if self.is_active and not self.email_confirmation.is_confirmed:
        #     raise RuntimeError("Email address is not confirmed!")

        super(VokoUser, self).save(*args, **kwargs)

        try:
            _ = self.email_confirmation
        except ObjectDoesNotExist:
            EmailConfirmation.objects.create(user=self)


class EmailConfirmation(TimeStampedModel):
    class Meta:
        verbose_name = "emailbevestiging"
        verbose_name_plural = "emailbevestigingen"

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

    def send_confirmation_mail(self):
        body = email_confirm_mail % {'URL': "http://leden.vokoutrecht.nl%s" % reverse('confirm_email', args=(self.pk,)),
                                     'first_name': self.user.first_name}
        send_mail('[VOKO Utrecht] Email-adres bevestigen', body, 'info@vokoutrecht.nl',
                  [self.user.email], fail_silently=False)

    def __unicode__(self):
        return "Confirmed: %s | user: %s | email: %s" % (self.is_confirmed, self.user, self.user.email)
