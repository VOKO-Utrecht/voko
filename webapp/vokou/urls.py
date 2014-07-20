from django.conf.urls import patterns, include, url
from django.contrib import admin
from accounts.views import LoginView

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'webapp.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^login/', LoginView.as_view()),
)
