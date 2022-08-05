# -*- coding: utf-8 -*-
import log
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin
from django.shortcuts import redirect
from accounts.forms import VokoUserCreationForm, VokoUserChangeForm
from accounts.models import (VokoUser, UserProfile, ReadOnlyVokoUser,
                             SleepingVokoUser, Address)
from finance.models import Payment
from mailing.helpers import get_template_by_id, render_mail_template, mail_user
from ordering.core import get_current_order_round
from ordering.models import Order
from django.utils.safestring import mark_safe
from hijack_admin.admin import HijackUserAdminMixin
from django.apps import apps
from constance import config


for model in apps.get_app_config('accounts').get_models():
    if model in (VokoUser, ReadOnlyVokoUser, SleepingVokoUser):
        continue
    admin.site.register(model)


def enable_user(modeladmin, request, queryset):
    for user in queryset:
        if not user.email_confirmation.is_confirmed or user.is_active:
            return

    queryset.update(can_activate=True)

    for user in queryset:
        # send mail
        mail_template = get_template_by_id(config.ACTIVATE_ACCOUNT_MAIL)
        (
            subject,
            html_message,
            plain_message,
            from_email
        ) = render_mail_template(
            mail_template, user=user
        )
        mail_user(user, subject, html_message, plain_message, from_email)
        log.log_event(
            user=user,
            event="User set to 'can_activate=True' and activation mail sent",
            extra=html_message
        )


enable_user.short_description = "Gebruikersactivatie na bezoek info-avond"


def force_confirm_email(modeladmin, request, queryset):
    for user in queryset:
        user.email_confirmation.is_confirmed = True
        user.email_confirmation.save()

        log.log_event(operator=request.user,
                      event="User's e-mail forcefully confirmed: %s" % user,
                      user=user)


force_confirm_email.short_description = "Forceer e-mailadres bevestiging"


def send_email_to_selected_users(modeladmin, request, queryset):
    user_ids = [user.pk for user in queryset]
    request.session['mailing_user_ids'] = user_ids
    return redirect("admin_choose_mail_template")


send_email_to_selected_users.short_description = "Verstuur E-mail"


def anonymize_user(modeladmin, request, queryset):
    """ Anonymize user to comply with GDPR regulations"""
    for user in queryset:
        # Set user to "sleeping mode"
        user.is_asleep = True

        # Anonymize email address
        user.email = "{}@anon.vokoutrecht.nl".format(user.id)

        # Anonymize name
        user.first_name = 'account'
        user.last_name = str(user.id)

        user.save()

        try:
            # Anonymize user profile
            profile = user.userprofile
            profile.phone_number = ''
            profile.notes = ''
            profile.save()

            # Anonymize address
            address = profile.address
            address.street_and_number = ''
            address.zip_code = '0000'
            address.city = ''
            address.save()

        except (UserProfile.DoesNotExist, Address.DoesNotExist):
            # Can happen with inactive users
            pass

        messages.add_message(
            request, messages.SUCCESS,
            'Gebruiker {} is op slaapstand gezet en geanonimiseerd.'.format(
                user.id)
        )


anonymize_user.short_description = 'Anonimiseer account'


class UserProfileInline(admin.StackedInline):
    model = UserProfile


def roles(self):
    # https://djangosnippets.org/snippets/1650/
    def short_name_part(name):
        return name[:2].upper()

    def short_name(name):
        name_parts = str(name).split(" ")
        short_name_parts = map(short_name_part, name_parts)
        return "_".join(short_name_parts)

    p = sorted(["<a title='%s'>%s</a>" % (
        x, short_name(x)) for x in self.groups.all()]
        )
    if self.user_permissions.count():
        p += ['+']
    value = ', '.join(p)
    return mark_safe("<nobr>%s</nobr>" % value)


roles.allow_tags = True
roles.short_description = 'Groups'


def phone(self):
    return self.userprofile.phone_number


def has_paid(self):
    return Payment.objects.filter(succeeded=True, order__user=self).exists()


has_paid.boolean = True
has_paid.short_description = "Has paid"


class HasPaidFilter(admin.SimpleListFilter):
    title = "has paid"
    parameter_name = 'has_paid'

    def lookups(self, request, model_admin):
        return [
            ("yes", "Ja"),
            ("no", "Nee")
        ]

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.distinct().filter(
                orders__payments__succeeded=True)
        elif self.value() == "no":
            return queryset.distinct().exclude(
                orders__payments__succeeded=True)
        else:
            return queryset.all()


class VokoUserBaseAdmin(UserAdmin):
    # Set the add/modify forms
    add_form = VokoUserCreationForm
    form = VokoUserChangeForm
    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ["first_name", "last_name", "email", phone,
                    "email_confirmed", "can_activate", "is_active", "is_staff",
                    has_paid,
                    "created", 'has_drivers_license', 'orders_round', 'debit',
                    'credit', 'total_orders', 'first_payment', roles]
    list_filter = ("is_staff", "is_superuser", "is_active",
                   "can_activate", HasPaidFilter, "groups")
    search_fields = ("email", 'first_name', 'last_name')
    ordering = ("first_name", "last_name")
    filter_horizontal = ("groups", "user_permissions",)
    fieldsets = (
        (None, {"fields": ("email", "password", "first_name",
                           "last_name", "is_asleep")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser",
                                    "groups", "user_permissions")}),
        ("Important dates", {"fields": ("last_login",)}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "first_name", "last_name")
            }
        ),
    )

    inlines = [
        UserProfileInline,
    ]

    def email_confirmed(self, obj):
        if obj.email_confirmation:
            return obj.email_confirmation.is_confirmed
        return False
    email_confirmed.boolean = True

    @staticmethod
    def orders_round(obj):
        # Orders in this round
        current_order_round = get_current_order_round()
        orders = Order.objects.filter(order_round=current_order_round,
                                      user=obj,
                                      paid=True).count()
        return orders

    @staticmethod
    def debit(obj):
        return obj.balance.debit()

    @staticmethod
    def credit(obj):
        return obj.balance.credit()

    @staticmethod
    def total_orders(obj):
        return Order.objects.filter(user=obj, paid=True).count()

    @staticmethod
    def first_payment(obj):
        try:
            return Payment.objects.filter(succeeded=True, order__user=obj)\
                .order_by('id').first().created
        except AttributeError:
            return

    @staticmethod
    def has_drivers_license(obj):
        return obj.userprofile.has_drivers_license
    has_drivers_license.boolean = True


class VokoUserAdmin(HijackUserAdminMixin, VokoUserBaseAdmin):
    list_display = VokoUserBaseAdmin.list_display + ['hijack_field']

    actions = (enable_user,
               force_confirm_email,
               send_email_to_selected_users,
               anonymize_user)


class ReadOnlyUserProfileInline(UserProfileInline):
    # See: https://code.djangoproject.com/ticket/17295
    def get_readonly_fields(self, request, obj=None):
        fields = [f.name for f in self.model._meta.get_fields()]
        return fields


class ReadOnlyVokoUserAdmin(VokoUserBaseAdmin):
    # See: https://code.djangoproject.com/ticket/17295
    def get_readonly_fields(self, request, obj=None):
        fields = [f.name for f in self.model._meta.get_fields()]
        return fields

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    inlines = [
        ReadOnlyUserProfileInline,
    ]


admin.site.register(VokoUser, VokoUserAdmin)
admin.site.register(ReadOnlyVokoUser, ReadOnlyVokoUserAdmin)
admin.site.register(SleepingVokoUser, VokoUserAdmin)
