from django.urls import path
from .views import Schedule, Shift
from distribution.views import Members, Groupmanager

urlpatterns = (
    path('schedule/', Schedule.as_view(), name="distribution_schedule"),
    path('shift/<slug>/', Shift.as_view(), name="shift"),
    path('members/', Members.as_view(), name="distribution_members"),
    path('groupmanager/', Groupmanager.as_view(), name="distribution_groupmanager")
)
