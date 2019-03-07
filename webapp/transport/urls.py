from django.conf.urls import url
from .views import Schedule, Ride

urlpatterns = (
    url(r'^schedule/$', Schedule.as_view(), name="schedule"),
    url(r'^ride/(?P<slug>[-\w]+)/$', Ride.as_view(), name="ride")
)
