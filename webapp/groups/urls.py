from django.conf.urls import url
from .views import Members

urlpatterns = (
    url(r'^members/$', Members.as_view(), name="members"),
)
