from django.conf.urls import url
from .views import Schedule, Shift
from distribution.views import Members, Groupmanager

urlpatterns = (
    url(r'^schedule/$', Schedule.as_view(), name="distribution_schedule"),
    url(r'^shift/(?P<slug>[-\w]+)/$', Shift.as_view(), name="shift"),
    url(r'^members/$', Members.as_view(), name="distribution_members"),
    url(r'^groupmanager/$', Groupmanager.as_view(), name="distribution_groupmanager")
)
