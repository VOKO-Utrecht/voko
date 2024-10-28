from django.urls import path
from .views import Members

urlpatterns = (
    path('members/', Members.as_view(), name="groups_members"),
)
