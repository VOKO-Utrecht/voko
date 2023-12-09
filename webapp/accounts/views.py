import logging
from datetime import datetime, timedelta

import log
import pytz
from accounts.forms import (ChangeProfileForm, PasswordResetForm,
                            RequestPasswordResetForm, VokoUserCreationForm,
                            VokoUserFinishForm)
from accounts.models import (EmailConfirmation, PasswordResetRequest,
                             UserProfile, VokoUser)
from agenda.models import PersistentEvent
from braces.views import (AnonymousRequiredMixin, GroupRequiredMixin,
                          LoginRequiredMixin)
from constance import config
from distribution.models import Shift
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import Group
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import (DetailView, FormView, ListView, TemplateView,
                                  UpdateView, View)
from ordering.core import get_or_create_order
from ordering.models import OrderRound
from transport.models import Ride
from news.models import Newsitem


class LoginView(AnonymousRequiredMixin, FormView):
    template_name = "accounts/login.html"
    form_class = AuthenticationForm

    def form_valid(self, form):
        login(self.request, form.get_user())
        next_url = settings.LOGIN_REDIRECT_URL
        try:
            next_url = self.request.GET["next"]
        except KeyError:
            pass

        return redirect(next_url)


class RegisterView(AnonymousRequiredMixin, FormView):
    template_name = "accounts/register.html"
    form_class = VokoUserCreationForm
    success_url = "/accounts/register/thanks"  # TODO: Reverse url

    def form_valid(self, form):
        user = form.save()
        user.email_confirmation.send_confirmation_mail()
        return super(RegisterView, self).form_valid(form)


class RegisterThanksView(AnonymousRequiredMixin, TemplateView):
    template_name = "accounts/register_thanks.html"


class WelcomeView(TemplateView):
    template_name = "accounts/welcome.html"


class LogoutView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        logout(request)
        return redirect("login")


class FinishRegistration(AnonymousRequiredMixin, UpdateView):
    template_name = "accounts/activate.html"
    success_url = "/accounts/welcome"
    form_class = VokoUserFinishForm

    def get_queryset(self):
        # We re-use the email confirmation token.
        return EmailConfirmation.objects.filter(
            is_confirmed=True,
            user__can_activate=True,
            user__is_active=False,
            token=self.kwargs["pk"],
        )

    def get_object(self, queryset=None):
        try:
            return self.get_queryset()[0].user
        except IndexError:
            raise Http404


class EmailConfirmView(AnonymousRequiredMixin, DetailView):
    model = EmailConfirmation

    def get_queryset(self):
        qs = super(EmailConfirmView, self).get_queryset()
        return qs.filter(is_confirmed=False)

    def get_context_data(self, **kwargs):
        self.get_object().confirm()
        return super(EmailConfirmView, self).get_context_data(**kwargs)


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/profile.html"

    def get_context_data(self, **kwargs):
        ctx = super(ProfileView, self).get_context_data(**kwargs)
        user = self.request.user
        ctx["unsubscribe_from_url"] = config.UNSUBSCRIBE_FORM_URL
        ctx["orders"] = user.orders.filter(paid=True).order_by("-pk")
        return ctx


class OrderHistory(LoginRequiredMixin, TemplateView):
    template_name = "accounts/order_history.html"

    def get_context_data(self, **kwargs):
        ctx = super(OrderHistory, self).get_context_data(**kwargs)
        user = self.request.user

        ctx["orders"] = user.orders.filter(paid=True).order_by("-pk")
        ctx["balances"] = user.balance.all().order_by("-pk")
        return ctx


class OverView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/overview.html"

    def get_context_data(self, **kwargs):
        ctx = super(OverView, self).get_context_data(**kwargs)
        user = self.request.user

        if user.id:
            # TODO: this line might be obsolete
            get_or_create_order(user)

        ctx["orders"] = user.orders.filter(paid=True).order_by("-pk")
        ctx["balances"] = user.balance.all().order_by("-pk")
        ctx["events"] = self._getAllEvents()

        # Show published news, published max 60 days ago. Order by publish date (desc)
        ctx['news'] = Newsitem.objects.filter(Q(publish=True) & Q(publish_date__lte=datetime.now(pytz.utc))
                                              & Q(publish_date__gt=datetime.now(pytz.utc)
                                                  - timedelta(days=60))).order_by("-publish_date")
        return ctx

    def current_order_round(self):
        return self.request.current_order_round

    def _getAllEvents(self):
        user = self.request.user
        myevents = []
        self._get_agenda_items(myevents)
        self._get_shifts(user, myevents)
        self._get_rides(user, myevents)
        self._get_coordinator_shifts(user, myevents)
        self._get_rounds(myevents)

        myevents.sort(key=lambda e: (e.date, e.time))
        return myevents

    def _get_rounds(self, myevents):
        # gets scheduled rounds until 60 days in future
        rounds = OrderRound.objects.filter(
            Q(open_for_orders__gt=datetime.now(pytz.utc))
            & Q(open_for_orders__lt=datetime.now(pytz.utc) + timedelta(days=60))
        )
        for r in rounds:
            try:
                myevents.append(r.as_event())
            except Exception as err:
                logging.log(logging.ERROR, err)

    def _get_coordinator_shifts(self, user, myevents):
        # get scheduled coordinator shifts for current user
        # from now until 60 days in future
        coords = OrderRound.objects.filter(
            Q(open_for_orders__gt=datetime.now(pytz.utc))
            & Q(open_for_orders__lt=datetime.now(pytz.utc) + timedelta(days=60))
            & (Q(distribution_coordinator=user) | Q(transport_coordinator=user))
        )
        for c in coords:
            try:
                event = c.as_event()
                event.is_shift = True
                if user == c.distribution_coordinator:
                    event.title = f"Uitdeelcoordinator ronde {c.id}"
                else:
                    event.title = f"Transportcoordinator ronde {c.id}"
                myevents.append(event)
            except Exception as err:
                logging.log(logging.ERROR, err)

    def _get_rides(self, user, myevents):
        # gets scheduled rides for current user
        # from now until 60 days in future
        rides = Ride.objects.filter(Q(driver__in=[user]) | Q(codriver__in=[user]))
        for r in rides:
            try:
                if r.date > datetime.now(pytz.utc) and r.date < datetime.now(pytz.utc) + timedelta(days=60):
                    myevents.append(r.as_event())
            except Exception as err:
                logging.log(logging.ERROR, err)

    def _get_shifts(self, user, myevents):
        # gets scheduled (distribution) shifts for current user
        # from now until 60 days in future
        shifts = Shift.objects.filter(members__in=[user])
        for s in shifts:
            try:
                if s.date > datetime.now(pytz.utc) and s.date < datetime.now(pytz.utc) + timedelta(days=60):
                    myevents.append(s.as_event())
            except Exception as err:
                logging.log(logging.ERROR, err)

    def _get_agenda_items(self, myevents):
        events = PersistentEvent.objects.filter(date__gt=datetime.now(pytz.utc))
        for e in events:
            try:
                myevents.append(e)
            except Exception as err:
                logging.log(logging.ERROR, err)


class RequestPasswordResetView(AnonymousRequiredMixin, FormView):
    # TODO: Rate limit

    template_name = "accounts/passwordreset.html"
    form_class = RequestPasswordResetForm
    success_url = "done"

    def form_valid(self, form):
        try:
            user = VokoUser.objects.get(email=form.cleaned_data["email"].lower())
            request = PasswordResetRequest(user=user)
            request.save()
            request.send_email()

        except VokoUser.DoesNotExist:
            # Do not notify user
            log.log_event(
                event="Password reset requested for unknown email address: %s"
                % form.cleaned_data["email"]
            )

        return super(RequestPasswordResetView, self).form_valid(form)


class PasswordResetRequestDoneView(AnonymousRequiredMixin, TemplateView):
    template_name = "accounts/passwordreset_requested.html"


class PasswordResetView(AnonymousRequiredMixin, FormView, DetailView):
    model = PasswordResetRequest
    template_name = "accounts/passwordreset_reset.html"
    form_class = PasswordResetForm
    success_url = "../finished"

    def get_queryset(self):
        qs = super(PasswordResetView, self).get_queryset()
        return qs.filter(is_used=False)

    def get_context_data(self, **kwargs):
        if not self.get_object().is_usable:
            raise Http404

        context = super(PasswordResetView, self).get_context_data(**kwargs)
        context["form"] = self.form_class()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.form_class(request.POST)

        if form.is_valid():
            with transaction.atomic():
                self.object.is_used = True
                self.object.save()
                self.object.user.set_password(form.cleaned_data["password1"])
                self.object.user.save()
            return self.form_valid(form)

        else:
            return self.form_invalid(form)


class PasswordResetFinishedView(AnonymousRequiredMixin, TemplateView):
    template_name = "accounts/passwordreset_finished.html"


class EditProfileView(LoginRequiredMixin, UpdateView):
    form_class = ChangeProfileForm
    success_url = "/accounts/profile"
    template_name = "accounts/update_profile.html"

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, "Je profiel is aangepast.")
        return super(EditProfileView, self).form_valid(form)


class Contact(LoginRequiredMixin, ListView):
    template_name = "accounts/contact.html"
    groups_to_show = {
        "ADMIN_GROUP",
        "TRANSPORT_GROUP",
        "DISTRIBUTION_GROUP",
        "FARMERS_GROUP",
        "IT_GROUP",
        "PROMO_GROUP",
    }

    def _get_groups(self):
        group_ids = []
        for name in self.groups_to_show:
            id = getattr(config, name)
            group_ids.append(id)
        return Group.objects.filter(pk__in=group_ids)

    def get_queryset(self):
        groups = self._get_groups()
        queryset = []
        for group in groups:
            try:
                contact = VokoUser.objects.get(userprofile__contact_person=group.id)
            except VokoUser.DoesNotExist:
                contact = None
            my_group = {"group": group, "contact": contact}
            queryset.append(my_group)
        return queryset


class EditCoordinatorRemarksView(LoginRequiredMixin, GroupRequiredMixin, UpdateView):
    group_required = "Transportcoordinatoren"
    template_name = "accounts/coordinator/remarks.html"
    model = UserProfile
    fields = ["coordinator_remarks"]
    success_url = "/transport/members"  # make this dynamic depending on starting on transport or distribution
