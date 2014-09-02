from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.models.loading import get_models, get_app
from accounts.forms import VokoUserCreationForm, VokoUserChangeForm
from accounts.mails import user_enable_mail
from accounts.models import VokoUser

for model in get_models(get_app('accounts')):
    if model == VokoUser:
        continue
    admin.site.register(model)


def enable_user(modeladmin, request, queryset):
    for user in queryset:
        if not user.email_confirmation.is_confirmed or user.is_active:
            return

    queryset.update(can_activate=True)

    for user in queryset:
            ## send mail
            body = user_enable_mail % {'URL': "http://leden.vokoutrecht.nl%s"
                                              % reverse('finish_registration', args=(user.email_confirmation.token,)),
                                       'first_name': user.first_name}
            send_mail('[VOKO Utrecht] Account activeren', body,
                      'info@vokoutrecht.nl', [user.email], fail_silently=False)


enable_user.short_description = "Gebruikersactivatie na bezoek info-avond"


class VokoUserAdmin(UserAdmin):
    # Set the add/modify forms
    add_form = VokoUserCreationForm
    form = VokoUserChangeForm
    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ("created", "email", "email_confirmed", "can_activate", "is_active", "is_staff", "first_name", "last_name")
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("email",)
    ordering = ("created", )
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

    actions = (enable_user,)

    def email_confirmed(self, obj):
        if obj.email_confirmation:
            return obj.email_confirmation.is_confirmed
        return False
    email_confirmed.boolean = True

admin.site.register(VokoUser, VokoUserAdmin)

