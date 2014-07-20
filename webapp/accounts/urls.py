from django.conf.urls import patterns, url
from .views import LoginView, RegisterView, PasswordResetView

urlpatterns = patterns('',
    url(r'^login/', LoginView.as_view()),
    url(r'^register/', RegisterView.as_view()),
    url(r'^passwordreset/', PasswordResetView.as_view()),
)