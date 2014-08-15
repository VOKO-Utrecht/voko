from django import forms
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.db import transaction
from .models import VokoUser, Address, UserProfile

# Custom user forms based on examples from Two Scoops of Django.


class VokoUserCreationForm(forms.ModelForm):
    zip_code = forms.CharField(label="Postcode", widget=forms.TextInput)

    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Password confirmation", widget=forms.PasswordInput)

    class Meta:
        model = VokoUser
        fields = ("email", "first_name", "last_name")

    def clean_password2(self):
        # Check that the two password entries match
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")

        if password1 and password2 and password1 != password2:
            msg = "Passwords don't match"
            raise forms.ValidationError(msg)

        return password2

    # TODO: clean_zip_code

    def save(self, commit=True):
        with transaction.atomic():
            # Save zip code in address
            address = Address.objects.create(zip_code=self.cleaned_data['zip_code'])

            # Create user
            user = super(VokoUserCreationForm, self).save(commit=False)
            user.set_password(self.cleaned_data["password1"])

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


class VokoUserAdmin(UserAdmin):
    # Set the add/modify forms
    add_form = VokoUserCreationForm
    form = VokoUserChangeForm
    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ("email", "is_staff")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("email",)
    ordering = ("email",)
    filter_horizontal = ("groups", "user_permissions",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (None, {
        "classes": ("wide",),
        "fields": ("email",
        "password1", "password2")}
        ),
    )

