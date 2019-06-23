from django.conf.urls import url
from .views import Schedule, Shift

urlpatterns = (
    url(r'^schedule/$', Schedule.as_view(), name="schedule"),
    url(r'^shift/(?P<slug>[-\w]+)/$', Shift.as_view(), name="shift")
)
