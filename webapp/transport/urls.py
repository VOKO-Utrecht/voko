from django.urls import path
from .views import Schedule, Ride, Cars, Groupmanager, Members

urlpatterns = (
    path("schedule/", Schedule.as_view(), name="schedule"),
    path("ride/<slug:slug>/", Ride.as_view(), name="ride"),
    path("cars/", Cars.as_view(), name="cars"),
    path("members/", Members.as_view(), name="transport_members"),
    path("groupmanager/", Groupmanager.as_view(), name="transport_groupmanager"),
)
