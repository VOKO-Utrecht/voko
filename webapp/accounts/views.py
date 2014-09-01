from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.http import Http404
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import FormView, DetailView, UpdateView, TemplateView
from accounts.forms import VokoUserCreationForm, VokoUserFinishForm
from accounts.models import EmailConfirmation, VokoUser
from django.conf import settings


class LoginView(FormView):
    template_name = "accounts/login.html"
    form_class = AuthenticationForm

    def form_valid(self, form):
        login(self.request, form.get_user())
        return redirect(settings.LOGIN_REDIRECT_URL)


class RegisterView(FormView):
    template_name = "accounts/register.html"
    form_class = VokoUserCreationForm
    success_url = "/accounts/register/thanks"  # TODO: Reverse url

    def get_context_data(self, **kwargs):
        context = super(FormView, self).get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        user = form.save()
        user.email_confirmation.send_confirmation_mail()
        return super(RegisterView, self).form_valid(form)


class RegisterThanksView(TemplateView):
    template_name = "accounts/register_thanks.html"


class FinishRegistration(UpdateView):
    template_name = "accounts/activate.html"
    success_url = "/accounts/welcome"
    form_class = VokoUserFinishForm

    def get_queryset(self):
        # We re-use the email confirmation token.
        return EmailConfirmation.objects.filter(is_confirmed=True, user__can_activate=True,
                                                user__is_active=False, token=self.kwargs['pk'])

    def get_object(self, queryset=None):
        try:
            return self.get_queryset()[0].user
        except IndexError:
            raise Http404


class PasswordResetView(FormView):
    template_name = "accounts/passwordreset.html"
    form_class = PasswordResetForm
    success_url = "/todo"


class EmailConfirmView(DetailView):
    model = EmailConfirmation

    def get_queryset(self):
        qs = super(EmailConfirmView, self).get_queryset()
        return qs.filter(is_confirmed=False)

    def get_context_data(self, **kwargs):
        self.get_object().confirm()
        return super(EmailConfirmView, self).get_context_data(**kwargs)

