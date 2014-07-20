from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
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

    def form_valid(self, form):
        # This method is called when valid form data has been POSTed.
        # It should return an HttpResponse.
        form.save()
        return super(RegisterView, self).form_valid(form)


class PasswordResetView(FormView):
    template_name = "accounts/passwordreset.html"
    form_class = PasswordResetForm
    success_url = "/todo"