from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.models.loading import get_models, get_app
from accounts.forms import VokoUserCreationForm, VokoUserChangeForm
from accounts.mails import user_enable_mail, eerste_bestelronde_mail_plain, \
    eerste_bestelronde_mail_html, order_reminder_mail
from accounts.models import VokoUser, UserProfile

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


def force_confirm_email(modeladmin, request, queryset):
    for user in queryset:
        user.email_confirmation.is_confirmed = True
        user.email_confirmation.save()

force_confirm_email.short_description = "Forceer e-mailadres bevestiging"


def send_first_order_mail(modeladmin, request, queryset):
    for user in queryset:
        plain_body = eerste_bestelronde_mail_plain % {'first_name': user.first_name}
        html_body = eerste_bestelronde_mail_html % {'first_name': user.first_name}

        send_mail('[VOKO Utrecht] Eerste bestelronde', message=plain_body, html_message=html_body,
                  from_email='VOKO Utrecht <info@vokoutrecht.nl>', recipient_list=[user.email], fail_silently=False)
send_first_order_mail.short_description = "EERSTE BESTELRONDE MAIL"


def send_first_order_reminder_mail(modeladmin, request, queryset):
    for user in queryset:
        plain_body = order_reminder_mail % {'first_name': user.first_name}

        send_mail('VOKO Utrecht - Herinnering: bestellen mogelijk tot 19/9/14, 18.00 uur', message=plain_body,
                  from_email='VOKO Utrecht <info@vokoutrecht.nl>', recipient_list=[user.email], fail_silently=False)
send_first_order_reminder_mail.short_description = "EERSTE BESTELRONDE MAIL REMINDER"


class UserProfileInline(admin.StackedInline):
    model = UserProfile


class VokoUserAdmin(UserAdmin):
    # Set the add/modify forms
    add_form = VokoUserCreationForm
    form = VokoUserChangeForm
    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ("first_name", "last_name", "email", "email_confirmed", "can_activate", "is_active", "is_staff", "created",)
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("email", 'first_name', 'last_name')
    ordering = ("-created", )
    filter_horizontal = ("groups", "user_permissions",)
    fieldsets = (
        (None, {"fields": ("email", "password", "first_name", "last_name")}),
        ("Permissions", {"fields": ("can_activate", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (None, {
        "classes": ("wide",),
        "fields": ("email",
        "first_name", "last_name")}
        ),
    )

    inlines = [
        UserProfileInline,
    ]

    actions = (enable_user, force_confirm_email, send_first_order_mail, send_first_order_reminder_mail)

    def email_confirmed(self, obj):
        if obj.email_confirmation:
            return obj.email_confirmation.is_confirmed
        return False
    email_confirmed.boolean = True

admin.site.register(VokoUser, VokoUserAdmin)

