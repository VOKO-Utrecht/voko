from django.urls import path
from .views import DocumentOverview, DocumentDownload

urlpatterns = (
    path("download/<slug:slug>/", DocumentDownload.as_view(), name="docs.document_download"),
    path("", DocumentOverview.as_view(), name="docs.document_overview"),
)
