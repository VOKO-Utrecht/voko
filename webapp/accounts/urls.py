from django.conf.urls import patterns, url
from .views import LoginView, RegisterView, RequestPasswordResetView, EmailConfirmView, FinishRegistration, RegisterThanksView, \
    WelcomeView, OverView, PasswordResetRequestDoneView, PasswordResetView, PasswordResetFinishedView, LogoutView, \
    EditProfileView

urlpatterns = patterns('',
    url(r'^login/$', LoginView.as_view(), name="login"),
    url(r'^logout/$', LogoutView.as_view(), name="logout"),
    url(r'^register/$', RegisterView.as_view(), name="register"),
    url(r'^register/thanks/$', RegisterThanksView.as_view(), name="register_thanks"),
    url(r'^register/confirm/(?P<pk>[0-9a-zA-Z\-]+)$', EmailConfirmView.as_view(), name="confirm_email"),
    url(r'^register/finish/(?P<pk>[0-9a-zA-Z\-]+)$', FinishRegistration.as_view(), name="finish_registration"),
    url(r'^passwordreset/$', RequestPasswordResetView.as_view(), name="password_reset"),
    url(r'^passwordreset/done/$', PasswordResetRequestDoneView.as_view()),
    url(r'^passwordreset/finished/$', PasswordResetFinishedView.as_view()),
    url(r'^passwordreset/reset/(?P<pk>[0-9a-zA-Z\-]+)$', PasswordResetView.as_view(), name="reset_pass"),
    url(r'^welcome/$', WelcomeView.as_view()),
    url(r'^overview/$', OverView.as_view(), name='overview'),
    url(r'^profile/$', EditProfileView.as_view(), name='profile'),
)