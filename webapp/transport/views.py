from braces.views import LoginRequiredMixin
from django.views.generic import (DetailView, ListView)
from transport import models
from django.db.models import Q
import datetime
from transport.mixins import UserIsInvolvedMixin


class Schedule(LoginRequiredMixin, ListView):
    template_name = "transport/schedule.html"

    def get_queryset(self):
        user = self.request.user
        return models.Ride.objects.filter(
            Q(driver=user) |
            Q(codriver=user) |
            Q(coordinators__id__exact=user.id)
        ).filter(
            order_round__collect_datetime__gte=datetime.date.today()
        ).order_by("-id")


class Ride(LoginRequiredMixin, UserIsInvolvedMixin, DetailView):
    template_name = "transport/ride.html"
    model = models.Ride
