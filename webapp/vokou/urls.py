from django.conf import settings
from django.conf.urls import include, url
from django.contrib import admin
import accounts.urls
import docs.urls
import transport.urls
import finance.urls
import mailing.urls
import ordering.urls
import ordering.admin_urls
import api.urls
import distribution.urls
from vokou.views import HomeView, PrivacyStatementView, RegulationsView

urlpatterns = [
    url(r'^admin/mailing/', include(mailing.urls)),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/', include(accounts.urls)),
    url(r'^ordering/admin/', include(ordering.admin_urls)),
    url(r'^ordering/', include(ordering.urls)),
    url(r'^finance/', include(finance.urls)),
    url(r'^docs/', include(docs.urls)),
    url(r'^transport/', include(transport.urls)),
    url(r'^api/', include(api.urls)),
    url(r'^distribution/', include(distribution.urls)),
    url(r'^tinymce/', include('tinymce.urls')),
    url(r'^hijack/', include('hijack.urls')),
    url(r'^regulations/', RegulationsView.as_view(), name="regulations"),
    url(r'^privacy/', PrivacyStatementView.as_view(), name="privacy"),
    url(r'^$', HomeView.as_view(), name="home"),
]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
