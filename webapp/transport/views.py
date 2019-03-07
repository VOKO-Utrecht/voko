from braces.views import LoginRequiredMixin
from django.views.generic import (DetailView, ListView)
from .models import Route, Ride
from django.conf import settings
import log
from ordering.core import get_or_create_order
from django.db.models import Q
import datetime

class Schedule(LoginRequiredMixin, ListView):
    template_name = "transport/schedule.html"

    def get_queryset(self):
        user = self.request.user
        return Ride.objects.filter(
            Q(driver=user) | Q(codriver=user)
        ).filter(
            order_round__collect_datetime__gte=datetime.date.today()
        ).order_by("-id")
