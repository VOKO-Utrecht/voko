from django.contrib.auth.forms import AuthenticationForm
from django.views.generic import FormView
from accounts.forms import VokoUserCreationForm


class LoginView(FormView):
    template_name = "accounts/login.html"
    form_class = AuthenticationForm
    success_url = "/welcome/"


class RegisterView(FormView):
    template_name = "accounts/register.html"
    form_class = VokoUserCreationForm
    success_url = "/todo"