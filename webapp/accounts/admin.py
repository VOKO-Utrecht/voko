# -*- coding: utf-8 -*-
import log
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.mail import send_mail
from django.db.models.loading import get_models, get_app
from django.shortcuts import redirect
from accounts.forms import VokoUserCreationForm, VokoUserChangeForm
from accounts.models import VokoUser, UserProfile
from mailing.helpers import get_template_by_id, render_mail_template
from ordering.core import get_current_order_round
from ordering.models import Order
from django.utils.safestring import mark_safe
from hijack.admin import HijackUserAdminMixin


ACTIVATE_ACCOUNT_MAILTEMPLATE_ID = 1

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
                      event="User's e-mail forcefully confirmet: %s" % user,
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
    short_name = lambda x: unicode(x)[:3].upper()
    p = sorted([u"<a title='%s'>%s</a>" % (x, short_name(x)) for x in self.groups.all()])
    if self.user_permissions.count():
        p += ['+']
    value = ', '.join(p)
    return mark_safe("<nobr>%s</nobr>" % value)
roles.allow_tags = True
roles.short_description = u'Groups'


def phone(self):
    return self.userprofile.phone_number


class VokoUserAdmin(UserAdmin, HijackUserAdminMixin):
    # Set the add/modify forms
    add_form = VokoUserCreationForm
    form = VokoUserChangeForm
    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ("first_name", "last_name", "email", phone, "email_confirmed", "can_activate", "is_active", "is_staff",
                    "created", 'orders_round', 'debit', 'credit', 'total_orders', roles, ) # 'hijack_field'
    list_filter = ("is_staff", "is_superuser", "is_active", "groups")
    search_fields = ("email", 'first_name', 'last_name')
    ordering = ("-created", )
    filter_horizontal = ("groups", "user_permissions",)
    fieldsets = (
        (None, {"fields": ("email", "password", "first_name", "last_name")}),
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
                                      finalized=True).count()
        return orders

    def debit(self, obj):
        return obj.balance.debit()

    def credit(self, obj):
        return obj.balance.credit()

    def total_orders(self, obj):
        return Order.objects.filter(user=obj, finalized=True).count()

admin.site.register(VokoUser, VokoUserAdmin)

