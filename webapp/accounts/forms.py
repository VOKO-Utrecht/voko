from captcha.fields import ReCaptchaField
from captcha.widgets import ReCaptchaV2Checkbox
from django import forms
from django.conf import settings
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.mail import mail_admins
from django.db import transaction
import log
from .models import VokoUser, UserProfile
from pytz import UTC
from datetime import datetime
from django.contrib.auth.models import Group

# Custom user forms based on examples from Two Scoops of Django.


class VokoUserCreationForm(forms.ModelForm):
    class Meta:
        model = VokoUser
        fields = ("email", "first_name", "last_name")

    if settings.CAPTCHA_ENABLED:
        captcha = ReCaptchaField(widget=ReCaptchaV2Checkbox)

    def save(self, commit=True):
        # Create user
        user = super(VokoUserCreationForm, self).save(commit=False)

        # Standardize on lowercase email address.
        user.email = user.email.lower()

        if commit:
            user.save()

        return user


class VokoUserFinishForm(forms.ModelForm):
    class Meta:
        model = VokoUser
        fields = ()

    phone_number = forms.CharField(
        label="Telefoonnummer",
        widget=forms.TextInput,
        required=False,
        max_length=25
    )

    password1 = forms.CharField(
        label="Wachtwoord",
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label="Wachtwoord (bevestiging)",
        widget=forms.PasswordInput
    )

    notes = forms.CharField(
        label="Antwoorden op bovenstaande vragen",
        widget=forms.Textarea
    )

    has_drivers_license = forms.BooleanField(
        label='Ik heb een rijbewijs',
        required=False
    )

    accept_terms_and_privacy = forms.BooleanField(
        label="Ik heb het Reglement en het Privacy Statement van "
              "VOKO Utrecht gelezen en ga met beiden akkoord.",
        required=True
    )

    def clean_password2(self):
        """ Check that the two password entries match """
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            msg = "Wachtwoorden zijn niet identiek!"
            raise forms.ValidationError(msg)

        return password2

    # TODO: clean phone number

    @staticmethod
    def _notify_admins_about_activated_user(user):
        # This is most likely temporary
        message = """Hoi!

Gebruiker %s heeft zojuist zijn/haar registratie afgerond..
""" % user

        mail_admins("Gebruiker %s is geactiveerd" % user, message,
                    fail_silently=True)

    def save(self, commit=True):
        with transaction.atomic():
            # Create user
            user = super(VokoUserFinishForm, self).save(commit=False)
            user.set_password(self.cleaned_data["password1"])
            user.is_active = True
            user.activated = datetime.now(UTC)

            if commit:
                user.save()

            UserProfile.objects.create(
                user=user,
                notes=self.cleaned_data['notes'],
                phone_number=self.cleaned_data['phone_number']
            )

            self._notify_admins_about_activated_user(user)
            log.log_event(user=user, event="User finished registration")

        return user


class VokoUserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = VokoUser
        exclude = []

    def clean_password(self):
        # Regardless of what the user provides, return the
        # initial value. This is done here, rather than on
        # the field, because the field does not have access
        # to the initial value
        return self.initial["password"]


class RequestPasswordResetForm(forms.Form):
    email = forms.EmailField(label="Email-adres", widget=forms.TextInput)


class PasswordResetForm(forms.Form):
    password1 = forms.CharField(
        label="Wachtwoord",
        widget=forms.PasswordInput
    )
    password2 = forms.CharField(
        label="Wachtwoord (bevestiging)",
        widget=forms.PasswordInput
    )

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            msg = "Wachtwoorden zijn niet identiek!"
            raise forms.ValidationError(msg)

        return password2


class ChangeProfileForm(forms.ModelForm):
    class Meta:
        model = VokoUser
        fields = ('first_name', 'last_name', )

    phone_number = forms.CharField(
        label="Telefoonnummer",
        widget=forms.TextInput,
        required=False
    )

    has_drivers_license = forms.BooleanField(
        label='Ik heb een rijbewijs',
        required=False
    )

    contact_person = forms.ModelChoiceField(
        queryset=Group.objects.all(),
        label="Contactpersoon voor",
        required=False,
        help_text=("Dit zet je contactgegevens op contactpagina van leden"
                   "site.")
    )

    password1 = forms.CharField(
        label="Wachtwoord (alleen invullen als je deze wilt wijzigen)",
        widget=forms.PasswordInput,
        required=False
    )
    password2 = forms.CharField(
        label=("Wachtwoord (bevestiging; alleen invullen "
               "als je deze wilt wijzigen)"),
        widget=forms.PasswordInput,
        required=False
    )

    shares_car = forms.BooleanField(
        label=("Ik heb een redelijk grote auto die leden kunnen lenen voor "
               "transport"),
        required=False,
        help_text=("Dit zet je contactgegevens op transport pagina's van de "
                   "ledensite")
    )
    car_neighborhood = forms.CharField(
        label="Buurt waar de auto staat",
        widget=forms.TextInput,
        required=False
    )
    car_type = forms.CharField(
        label="Type auto",
        widget=forms.TextInput,
        required=False
    )
    particularities = forms.CharField(
        label="Bijzonderheden",
        required=False,
        widget=forms.Textarea,
        help_text=("Informatie over beschikbaarheid of andere bijzonderheden."
                   "Zichtbaar voor andere VOKO leden.")
    )

    # TODO: Notes and e-mail address cannot be changed atm.

    def __init__(self, data=None, *args, **kwargs):
        super(ChangeProfileForm, self).__init__(data=data, *args, **kwargs)
        # This is hacky. Should use Inline Formset.
        self.fields['phone_number'].initial = (
            self.instance.userprofile.phone_number)
        self.fields['has_drivers_license'].initial = (
            self.instance.userprofile.has_drivers_license)
        self.fields['contact_person'].initial = (
            self.instance.userprofile.contact_person)
        self.fields['shares_car'].initial = (
            self.instance.userprofile.shares_car)
        self.fields['car_neighborhood'].initial = (
            self.instance.userprofile.car_neighborhood)
        self.fields['car_type'].initial = (
            self.instance.userprofile.car_type)
        self.fields['particularities'].initial = (
            self.instance.userprofile.particularities)

        # If shares car, set more fields as required
        if data and data.get('shares_car', None) is not None:
            self.fields['car_neighborhood'].required = True
            self.fields['car_type'].required = True

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            msg = "Wachtwoorden zijn niet identiek!"
            raise forms.ValidationError(msg)

        return password2

    # TODO: clean phone number

    def save(self, commit=True):
        with transaction.atomic():
            # Update user
            user = super(ChangeProfileForm, self).save()

            if self.cleaned_data['password1']:
                user.set_password(self.cleaned_data["password1"])

            # Profile
            userprofile = user.userprofile
            userprofile.phone_number = self.cleaned_data['phone_number']
            userprofile.has_drivers_license = (
                self.cleaned_data['has_drivers_license'])
            userprofile.contact_person = self.cleaned_data['contact_person']
            userprofile.shares_car = self.cleaned_data['shares_car']
            userprofile.car_neighborhood = (
                self.cleaned_data['car_neighborhood'])
            userprofile.car_type = self.cleaned_data['car_type']
            userprofile.particularities = self.cleaned_data['particularities']

            if commit:
                user.save()
                userprofile.save()

            log.log_event(user=user, event="User changed profile")

        return user
