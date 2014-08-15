from django.conf.urls import patterns, include, url
from django.contrib import admin
import accounts.urls
import ordering.urls
from vokou.views import HomeView

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include(accounts.urls)),
    url(r'^ordering/', include(ordering.urls)),
    url(r'^$', HomeView.as_view(), name="home"),

)
