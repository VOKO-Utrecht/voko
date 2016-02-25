from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.core.mail import mail_admins
from django.db import transaction
import log
from .models import VokoUser, Address, UserProfile

# Custom user forms based on examples from Two Scoops of Django.


class VokoUserCreationForm(forms.ModelForm):
    class Meta:
        model = VokoUser
        fields = ("email", "first_name", "last_name")

    def save(self, commit=True):
        # Create user
        user = super(VokoUserCreationForm, self).save(commit=False)
        if commit:
            user.save()

        return user

    def clean_keep_empty(self):
        if self.cleaned_data['keep_empty']:
            raise forms.ValidationError("Er ging iets mis")  # Stay vague
        return self.cleaned_data['keep_empty']

    keep_empty = forms.CharField(required=False, label="Niet invullen")  # Used to mislead spam bots


class VokoUserFinishForm(forms.ModelForm):
    class Meta:
        model = VokoUser
        fields = ()

    zip_code = forms.CharField(label="Postcode", widget=forms.TextInput)
    phone_number = forms.CharField(label="Telefoonnummer (optioneel)", widget=forms.TextInput, required=False)

    password1 = forms.CharField(label="Wachtwoord", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Wachtwoord (bevestiging)", widget=forms.PasswordInput)

    notes = forms.CharField(label="Antwoorden op bovenstaande vragen", widget=forms.Textarea)

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            msg = "Wachtwoorden zijn niet identiek!"
            raise forms.ValidationError(msg)

        return password2

    # TODO: clean_zip_code and phone number

    def _notify_admins_about_activated_user(self, user):
        # This is most likely temporary
        message = """Hoi!

Gebruiker %s heeft zojuist zijn/haar registratie afgerond..
""" % user

        mail_admins("Gebruiker %s is geactiveerd" % user, message, fail_silently=True)

    def save(self, commit=True):
        with transaction.atomic():
            # Save zip code in address
            address = Address.objects.create(zip_code=self.cleaned_data['zip_code'])

            # Create user
            user = super(VokoUserFinishForm, self).save(commit=False)
            user.set_password(self.cleaned_data["password1"])
            user.is_active = True

            if commit:
                user.save()

            # Lastly, link the two
            UserProfile.objects.create(user=user, address=address,
                                       notes=self.cleaned_data['notes'],
                                       phone_number=self.cleaned_data['phone_number'])

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
    password1 = forms.CharField(label="Wachtwoord", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Wachtwoord (bevestiging)", widget=forms.PasswordInput)

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
        fields = ('first_name', 'last_name')

    zip_code = forms.CharField(label="Postcode", widget=forms.TextInput)
    phone_number = forms.CharField(label="Telefoonnummer (optioneel)", widget=forms.TextInput, required=False)

    password1 = forms.CharField(label="Wachtwoord (alleen invullen als je deze wilt wijzigen)", widget=forms.PasswordInput, required=False)
    password2 = forms.CharField(label="Wachtwoord (bevestiging; alleen invullen als je deze wilt wijzigen)", widget=forms.PasswordInput, required=False)

    # TODO: Notes and e-mail address cannot be changed atm.

    def __init__(self, *args, **kwargs):
        super(ChangeProfileForm, self).__init__(*args, **kwargs)
        self.fields['zip_code'].initial = self.instance.userprofile.address.zip_code
        self.fields['phone_number'].initial = self.instance.userprofile.phone_number

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            msg = "Wachtwoorden zijn niet identiek!"
            raise forms.ValidationError(msg)

        return password2

    # TODO: clean_zip_code and phone number

    def save(self, commit=True):
        with transaction.atomic():
            # Update user
            user = super(ChangeProfileForm, self).save()

            if self.cleaned_data['password1']:
                user.set_password(self.cleaned_data["password1"])

            # Profile
            userprofile = user.userprofile
            userprofile.phone_number = self.cleaned_data['phone_number']

            # And address
            address = user.userprofile.address
            address.zip_code = self.cleaned_data['zip_code']

            if commit:
                user.save()
                userprofile.save()
                address.save()

            log.log_event(user=user, event="User changed profile")

        return user
