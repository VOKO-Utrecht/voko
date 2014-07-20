from django.contrib.auth.forms import AuthenticationForm
from django.views.generic import TemplateView, FormView


class LoginView(FormView):
    template_name = "login.html"
    form_class = AuthenticationForm
    success_url = "/todo"