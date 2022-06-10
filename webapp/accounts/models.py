# -*- coding: utf-8 -*-
import pytz
from datetime import datetime, timedelta
from django.utils import timezone
from uuid import uuid4
from django.contrib.auth.models import (BaseUserManager, AbstractBaseUser,
                                        PermissionsMixin)
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.db import models
from django_extensions.db.models import TimeStampedModel
from django.conf import settings
from django.utils.translation import ugettext_lazy as _
from django.core.mail import mail_admins
from mailing.helpers import get_template_by_id, render_mail_template, mail_user
from constance import config


class Address(TimeStampedModel):
    class Meta:
        verbose_name = "adres"
        verbose_name_plural = "adressen"

    street_and_number = models.CharField(max_length=100, blank=True)
    zip_code = models.CharField(max_length=7)
    city = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return "%s - %s, %s" % (self.street_and_number,
                                self.zip_code,
                                self.city)


class UserProfile(TimeStampedModel):
    class Meta:
        verbose_name = "ledenprofiel"
        verbose_name_plural = "ledenprofielen"

    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                related_name="userprofile",
                                on_delete=models.CASCADE)
    address = models.ForeignKey(Address,
                                null=True,
                                blank=True,
                                on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=25, blank=True)
    notes = models.TextField()
    has_drivers_license = models.BooleanField(default=False)
    contact_person = models.OneToOneField(
        "auth.Group",
        verbose_name="Contactpersoon voor",
        help_text="Zet contactgegevens op contactpagina van leden site",
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    shares_car = models.BooleanField(
        default=False,
        verbose_name=("Ik heb een redelijk grote auto die leden kunnen lenen "
                      "voor transport"),
        help_text=("Dit zet je contactgegevens op transport pagina's van de "
                   "ledensite")
    )
    car_neighborhood = models.CharField(max_length=100, blank=True)
    car_type = models.CharField(max_length=100, blank=True)

    def __str__(self):
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
        user = self.create_user(email,
                                first_name,
                                last_name,
                                password=password)
        user.is_active = True
        user.is_admin = True
        user.is_staff = True
        user.is_superuser = True
        user.activated = timezone.now()
        user.save(using=self._db)
        return user

    # NOTE: Remove following lines when executing a
    # 'loaddata' management command (FIXME)
    def get_queryset(self):
        return super(VokoUserManager, self).get_queryset().filter(
            is_asleep=False
        )


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
    is_asleep = models.BooleanField(default=False,
                                    verbose_name="Sleeping (inactive) member")

    activated = models.DateTimeField(
        null=True,
        editable=False,
        help_text="When account was activated")

    objects = VokoUserManager()

    def get_full_name(self):
        return "%s %s" % (self.first_name, self.last_name)

    def get_short_name(self):
        return self.email

    def __str__(self):
        return self.get_full_name()

    def save(self, *args, **kwargs):
        # Disabled because this breaks admin login (TODO)
        # if self.is_active and not self.email_confirmation.is_confirmed:
        #     raise RuntimeError("Email address is not confirmed!")
        if self.pk is None:
            message = """Hoi! We hebben een nieuwe gebruiker: %s""" % self
            mail_admins("Nieuwe gebruiker: %s" % self, message,
                        fail_silently=True)

        super(VokoUser, self).save(*args, **kwargs)

        try:
            _ = self.email_confirmation  # noqa
        except ObjectDoesNotExist:
            EmailConfirmation.objects.create(user=self)

    def flat_groups(self):
        return self.groups.values_list("name", flat=True)


class EmailConfirmation(TimeStampedModel):
    class Meta:
        verbose_name = "emailbevestiging"
        verbose_name_plural = "emailbevestigingen"

    token = models.CharField(max_length=100, primary_key=True)
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                related_name="email_confirmation",
                                on_delete=models.CASCADE)
    is_confirmed = models.BooleanField(default=False)

    def save(self, **kwargs):
        if not self.token:
            self.token = str(uuid4())
        super(EmailConfirmation, self).save(**kwargs)

    def confirm(self):
        self.is_confirmed = True
        self.save()

    def send_confirmation_mail(self):
        mail_template = get_template_by_id(config.CONFIRM_MAIL)
        rendered_template_vars = render_mail_template(mail_template,
                                                      user=self.user)
        mail_user(self.user, *rendered_template_vars)

    def __str__(self):
        return "Confirmed: %s | user: %s | email: %s" % (
            self.is_confirmed,
            self.user.get_full_name(),
            self.user.email
        )


class PasswordResetRequest(TimeStampedModel):
    class Meta:
        verbose_name = "wachtwoordreset-aanvraag"
        verbose_name_plural = "wachtwoordreset-aanvragen"

    token = models.CharField(max_length=100, primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name="password_reset_requests",
                             on_delete=models.CASCADE)
    is_used = models.BooleanField(default=False)

    def save(self, **kwargs):
        if not self.token:
            self.token = str(uuid4())
        super(PasswordResetRequest, self).save(**kwargs)

    def send_email(self):
        mail_template = get_template_by_id(config.PASSWORD_RESET_MAIL)
        rendered_template_vars = render_mail_template(
            mail_template,
            user=self.user,
            url=settings.BASE_URL + reverse('reset_pass', args=(self.pk,))
        )
        mail_user(self.user, *rendered_template_vars)

    @property
    def is_usable(self):
        if self.is_used:
            return False

        # Time window of 24 hours to reset
        if (datetime.now(pytz.utc) - self.created) > timedelta(hours=24):
            return False

        return True

    def __str__(self):
        return "User: %s | Used: %s | Usable: %s" % (
            self.user,
            self.is_used,
            self.is_usable)


class ReadOnlyVokoUser(VokoUser):
    class Meta:
        proxy = True
        verbose_name = "Lid (read-only)"
        verbose_name_plural = "Leden (read-only)"


class SleepingVokoUserManager(VokoUserManager):
    def get_queryset(self):
        return super(BaseUserManager, self).get_queryset().filter(
            is_asleep=True
        )


class SleepingVokoUser(VokoUser):
    class Meta:
        proxy = True
        verbose_name = "Slapend lid"
        verbose_name_plural = "Slapende leden"

    objects = SleepingVokoUserManager()
