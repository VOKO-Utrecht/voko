from django.conf import settings
from django.urls import include, path
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
import groups.urls
import news.urls
from vokou.views import HomeView, PrivacyStatementView, RegulationsView

urlpatterns = [
    path("admin/mailing/", include(mailing.urls)),
    path("admin/", admin.site.urls),
    path("accounts/", include(accounts.urls)),
    path("ordering/admin/", include(ordering.admin_urls)),
    path("ordering/", include(ordering.urls)),
    path("finance/", include(finance.urls)),
    path("docs/", include(docs.urls)),
    path("transport/", include(transport.urls)),
    path("groups/", include(groups.urls)),
    path("news/", include(news.urls)),
    path("api/", include(api.urls)),
    path("distribution/", include(distribution.urls)),
    path("tinymce/", include("tinymce.urls")),
    path("hijack/", include("hijack.urls")),
    path("regulations/", RegulationsView.as_view(), name="regulations"),
    path("privacy/", PrivacyStatementView.as_view(), name="privacy"),
    path("", HomeView.as_view(), name="home"),
]

if settings.DEBUG:
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
