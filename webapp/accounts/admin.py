# -*- coding: utf-8 -*-
import log
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.contrib.admin.utils import flatten_fieldsets
from accounts.forms import VokoUserCreationForm, VokoUserChangeForm
from accounts.models import VokoUser, UserProfile, ReadOnlyVokoUser, SleepingVokoUser
from mailing.helpers import get_template_by_id, render_mail_template
from ordering.core import get_current_order_round
from ordering.models import Order
from django.utils.safestring import mark_safe
from hijack.admin import HijackUserAdminMixin
from django.apps import apps

ACTIVATE_ACCOUNT_MAILTEMPLATE_ID = 1


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
        ## send mail
        mail_template = get_template_by_id(ACTIVATE_ACCOUNT_MAILTEMPLATE_ID)
        subject, html_message, plain_message = render_mail_template(mail_template, user=user)
        send_mail(subject=subject,
                  message=plain_message,
                  from_email="VOKO Utrecht <info@vokoutrecht.nl>",
                  recipient_list=["%s <%s>" % (user.get_full_name(), user.email)],
                  html_message=html_message)
        log.log_event(user=user, event="User set to 'can_activate=True' and activation mail sent", extra=html_message)

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


class UserProfileInline(admin.StackedInline):
    model = UserProfile


def roles(self):
    # https://djangosnippets.org/snippets/1650/
    short_name = lambda x: str(x)[:3].upper()
    p = sorted(["<a title='%s'>%s</a>" % (x, short_name(x)) for x in self.groups.all()])
    if self.user_permissions.count():
        p += ['+']
    value = ', '.join(p)
    return mark_safe("<nobr>%s</nobr>" % value)
roles.allow_tags = True
roles.short_description = 'Groups'


def phone(self):
    return self.userprofile.phone_number


class VokoUserAdmin(HijackUserAdminMixin, UserAdmin):
    # Set the add/modify forms
    add_form = VokoUserCreationForm
    form = VokoUserChangeForm
    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ("first_name", "last_name", "email", phone, "email_confirmed", "can_activate", "is_active", "is_staff",
                    "created", 'orders_round', 'debit', 'credit', 'total_orders', roles, 'hijack_field')
    list_filter = ("is_staff", "is_superuser", "is_active", "can_activate", "groups")
    search_fields = ("email", 'first_name', 'last_name')
    ordering = ("-created", )
    filter_horizontal = ("groups", "user_permissions",)
    fieldsets = (
        (None, {"fields": ("email", "password", "first_name", "last_name", "is_asleep")}),
        ("Permissions", {"fields": ("is_staff", "is_superuser", "groups", "user_permissions")}),
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

    actions = (enable_user, force_confirm_email, send_email_to_selected_users)

    def email_confirmed(self, obj):
        if obj.email_confirmation:
            return obj.email_confirmation.is_confirmed
        return False
    email_confirmed.boolean = True

    def orders_round(self, obj):
        ## Orders in this round
        current_order_round = get_current_order_round()
        orders = Order.objects.filter(order_round=current_order_round,
                                      user=obj,
                                      paid=True).count()
        return orders

    def debit(self, obj):
        return obj.balance.debit()

    def credit(self, obj):
        return obj.balance.credit()

    def total_orders(self, obj):
        return Order.objects.filter(user=obj, paid=True).count()


class ReadOnlyVokoUserAdmin(VokoUserAdmin):
    # Source: https://code.djangoproject.com/ticket/17295
    def get_readonly_fields(self, request, obj=None):
        # untested, this could do:
        # readonly_fields = self.model._meta.get_all_field_names()
        # borrowed from ModelAdmin:
        if self.declared_fieldsets:
            fields = flatten_fieldsets(self.declared_fieldsets)
        else:
            form = self.get_formset(request, obj).form
            fields = form.base_fields.keys()
        return fields

    def has_add_permission(self, request):
        # Nobody is allowed to add
        return False

    def has_delete_permission(self, request, obj=None):
        # Nobody is allowed to delete
        return False

admin.site.register(VokoUser, VokoUserAdmin)
admin.site.register(ReadOnlyVokoUser, ReadOnlyVokoUserAdmin)
admin.site.register(SleepingVokoUser, VokoUserAdmin)
