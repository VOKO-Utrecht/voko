from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.db import transaction
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


class VokoUserFinishForm(forms.ModelForm):
    class Meta:
        model = VokoUser
        fields = ()

    zip_code = forms.CharField(label="Postcode", widget=forms.TextInput)

    password1 = forms.CharField(label="Wachtwoord", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Wachtwoord (bevestiging)", widget=forms.PasswordInput)

    notes = forms.CharField(label="Voorkeur", widget=forms.Textarea)

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            msg = "Wachtwoorden zijn niet identiek!"
            raise forms.ValidationError(msg)

        return password2

    # TODO: clean_zip_code

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
            UserProfile.objects.create(user=user, address=address)

        return user


class VokoUserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = VokoUser

    def clean_password(self):
        # Regardless of what the user provides, return the
        # initial value. This is done here, rather than on
        # the field, because the field does not have access
        # to the initial value
        return self.initial["password"]

