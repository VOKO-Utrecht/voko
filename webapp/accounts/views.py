from braces.views import AnonymousRequiredMixin, LoginRequiredMixin
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from django.http import Http404
from django.shortcuts import redirect
from django.views.generic import (FormView, DetailView, UpdateView,
                                  TemplateView, ListView, View)
from accounts.forms import (VokoUserCreationForm, VokoUserFinishForm,
                            RequestPasswordResetForm, PasswordResetForm,
                            ChangeProfileForm)
from accounts.models import EmailConfirmation, VokoUser, PasswordResetRequest
from django.conf import settings
import log
from ordering.core import get_or_create_order

class LoginView(AnonymousRequiredMixin, FormView):
    template_name = "accounts/login.html"
    form_class = AuthenticationForm

    def form_valid(self, form):
        login(self.request, form.get_user())
        next_url = settings.LOGIN_REDIRECT_URL
        try:
            next_url = self.request.GET['next']
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
        return redirect('login')


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
            token=self.kwargs['pk']
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


class OverView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/overview.html"

    def get_context_data(self, **kwargs):
        ctx = super(OverView, self).get_context_data(**kwargs)

        if self.request.user.id:
            # TODO: this line might be obsolete
            get_or_create_order(self.request.user)

        ctx['orders'] = self.request.user.orders.filter(
            paid=True).order_by("-pk")
        ctx['balances'] = self.request.user.balance.all().order_by('-pk')
        return ctx

    def current_order_round(self):
        return self.request.current_order_round


class RequestPasswordResetView(AnonymousRequiredMixin, FormView):
    # TODO: Rate limit

    template_name = "accounts/passwordreset.html"
    form_class = RequestPasswordResetForm
    success_url = "done"

    def form_valid(self, form):
        try:
            user = VokoUser.objects.get(
                email=form.cleaned_data['email'].lower()
            )
            request = PasswordResetRequest(user=user)
            request.save()
            request.send_email()

        except VokoUser.DoesNotExist:
            # Do not notify user
            log.log_event(
                event="Password reset requested for unknown email address: %s"
                      % form.cleaned_data['email']
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
        context['form'] = self.form_class()
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.form_class(request.POST)

        if form.is_valid():
            with transaction.atomic():
                self.object.is_used = True
                self.object.save()
                self.object.user.set_password(form.cleaned_data['password1'])
                self.object.user.save()
            return self.form_valid(form)

        else:
            return self.form_invalid(form)


class PasswordResetFinishedView(AnonymousRequiredMixin, TemplateView):
    template_name = "accounts/passwordreset_finished.html"


class EditProfileView(LoginRequiredMixin, UpdateView):
    form_class = ChangeProfileForm
    success_url = "/accounts/profile"
    template_name = "accounts/profile.html"

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS,
                             "Je profiel is aangepast.")
        return super(EditProfileView, self).form_valid(form)

class MemberList(LoginRequiredMixin, ListView):
    model = VokoUser
    template_name = "accounts/member_list.html"