from django.conf.urls import url
from .views import Schedule, Ride, Cars, Groupmanager, Members

urlpatterns = (
    url(r'^schedule/$', Schedule.as_view(), name="schedule"),
    url(r'^ride/(?P<slug>[-\w]+)/$', Ride.as_view(), name="ride"),
    url(r'^cars/$', Cars.as_view(), name="cars"),
    url(r'^members/$', Members.as_view(), name="members"),
    url(r'^groupmanager/$', Groupmanager.as_view(), name="groupmanager")
)
