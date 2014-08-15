from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.shortcuts import redirect
from django.views.generic import FormView, DetailView
from accounts.forms import VokoUserCreationForm
from accounts.models import EmailConfirmation
from vokou import settings


class LoginView(FormView):
    template_name = "accounts/login.html"
    form_class = AuthenticationForm

    def form_valid(self, form):
        login(self.request, form.get_user())
        return redirect(settings.LOGIN_REDIRECT_URL)


class RegisterView(FormView):
    template_name = "accounts/register.html"
    form_class = VokoUserCreationForm
    success_url = "/todo"

    def get_context_data(self, **kwargs):
        context = super(FormView, self).get_context_data(**kwargs)
        return context

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        user = form.save()
        user.email_confirmation.send_confirmation_mail()
        return super(RegisterView, self).form_valid(form)


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

