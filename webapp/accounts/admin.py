from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.db.models.loading import get_models, get_app
from accounts.forms import VokoUserCreationForm, VokoUserChangeForm
from accounts.models import VokoUser

for model in get_models(get_app('accounts')):
    if model == VokoUser:
        continue
    admin.site.register(model)


class VokoUserAdmin(UserAdmin):
    # Set the add/modify forms
    add_form = VokoUserCreationForm
    form = VokoUserChangeForm
    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ("created", "email", "is_staff", "can_activate", "is_active", "first_name", "last_name")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("email",)
    ordering = ("created",)
    filter_horizontal = ("groups", "user_permissions",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Permissions", {"fields": ("can_activate", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (None, {
        "classes": ("wide",),
        "fields": ("email",
        "password1", "password2")}
        ),
    )

admin.site.register(VokoUser, VokoUserAdmin)