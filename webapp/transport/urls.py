from django.conf.urls import url
from .views import Schedule

urlpatterns = (
    url(r'^schedule/$', Schedule.as_view(), name="schedule"),
    # url(r'^ride/(?P<pk>[0-9]+)/$', Ride.as_view(),
    #     name="ride")
)
