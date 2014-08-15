from django.conf.urls import patterns, url
from .views import LoginView, RegisterView, PasswordResetView, EmailConfirmView

urlpatterns = patterns('',
    url(r'^login/$', LoginView.as_view()),
    url(r'^register/$', RegisterView.as_view()),
    url(r'^register/confirm/(?P<pk>[0-9a-zA-Z]+)$', EmailConfirmView.as_view()),
    url(r'^passwordreset/$', PasswordResetView.as_view()),
)