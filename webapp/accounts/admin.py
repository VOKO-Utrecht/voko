from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.db.models.loading import get_models, get_app
from django.shortcuts import redirect
from accounts.forms import VokoUserCreationForm, VokoUserChangeForm
from accounts.mails import user_enable_mail
from accounts.models import VokoUser, UserProfile
from log import log_event
from ordering.core import get_current_order_round
from ordering.models import Order

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

        log_event(operator=request.user,
                  event="User set to 'can_activate': %s" % user)

enable_user.short_description = "Gebruikersactivatie na bezoek info-avond"


def force_confirm_email(modeladmin, request, queryset):
    for user in queryset:
        user.email_confirmation.is_confirmed = True
        user.email_confirmation.save()

force_confirm_email.short_description = "Forceer e-mailadres bevestiging"


def send_email_to_selected_users(modeladmin, request, queryset):
    user_ids = [user.pk for user in queryset]
    request.session['mailing_user_ids'] = user_ids
    return redirect("admin_choose_mail_template")


send_email_to_selected_users.short_description = "Verstuur E-mail"


class UserProfileInline(admin.StackedInline):
    model = UserProfile


class VokoUserAdmin(UserAdmin):
    # Set the add/modify forms
    add_form = VokoUserCreationForm
    form = VokoUserChangeForm
    # The fields to be used in displaying the User model.
    # These override the definitions on the base UserAdmin
    # that reference specific fields on auth.User.
    list_display = ("first_name", "last_name", "email", "email_confirmed", "can_activate", "is_active", "is_staff",
                    "created", 'finished_orders_curr_OR')
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

    current_order_round = get_current_order_round()

    def finished_orders_curr_OR(self, obj):
        orders = Order.objects.filter(order_round=self.current_order_round,
                                      user=obj,
                                      finalized=True).count()
        return orders
        # if orders:
        #     return True
        # return False
    # finished_orders_curr_OR.boolean = True


admin.site.register(VokoUser, VokoUserAdmin)

