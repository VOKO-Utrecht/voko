from django.conf.urls import patterns, include, url
from django.contrib import admin
from accounts.views import LoginView, RegisterView

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/login/', LoginView.as_view()),
    url(r'^accounts/register/', RegisterView.as_view()),
)
