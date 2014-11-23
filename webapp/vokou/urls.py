from django.conf.urls import patterns, include, url
from django.contrib import admin
import accounts.urls
import finance.urls
import mailing.urls
import ordering.urls
from vokou.views import HomeView

urlpatterns = patterns('',
    url(r'^admin/mailing/', include(mailing.urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include(accounts.urls)),
    url(r'^ordering/', include(ordering.urls)),
    url(r'^finance/', include(finance.urls)),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^$', HomeView.as_view(), name="home"),

)
