from django.conf.urls import url
from accounts import views

urlpatterns = (
    url(r'^login/$', views.LoginView.as_view(), name="login"),
    url(r'^logout/$', views.LogoutView.as_view(), name="logout"),

    url(r'^register/$', views.RegisterView.as_view(), name="register"),
    url(r'^register/thanks/$',
        views.RegisterThanksView.as_view(),
        name="register_thanks"),
    url(r'^register/confirm/(?P<pk>[0-9a-zA-Z\-]+)$',
        views.EmailConfirmView.as_view(),
        name="confirm_email"),
    url(r'^register/finish/(?P<pk>[0-9a-zA-Z\-]+)$',
        views.FinishRegistration.as_view(),
        name="finish_registration"),

    url(r'^passwordreset/$',
        views.RequestPasswordResetView.as_view(),
        name="password_reset"),
    url(r'^passwordreset/done/$',
        views.PasswordResetRequestDoneView.as_view()),
    url(r'^passwordreset/finished/$',
        views.PasswordResetFinishedView.as_view()),
    url(r'^passwordreset/reset/(?P<pk>[0-9a-zA-Z\-]+)$',
        views.PasswordResetView.as_view(),
        name="reset_pass"),

    url(r'^welcome/$', views.WelcomeView.as_view()),
    url(r'^overview/$', views.OverView.as_view(), name='overview'),
    url(r'^profile/$', views.EditProfileView.as_view(), name='profile'),
    url(r'^contact/$', views.Contact.as_view(), name='contact'),
)
