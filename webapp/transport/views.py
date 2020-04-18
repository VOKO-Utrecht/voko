from braces.views import LoginRequiredMixin
from django.views.generic import (DetailView, ListView)
from transport import models
from django.db.models import Q
import datetime
from transport.mixins import UserIsInvolvedMixin
from accounts.models import VokoUser


class Schedule(LoginRequiredMixin, ListView):
    template_name = "transport/schedule.html"

    def get_queryset(self):
        user = self.request.user

        if (user.groups.filter(name__in=['Transportcoordinatoren','Admin']).exists()):
            rides = models.Ride.objects.all()
        else:
            rides = models.Ride.objects.filter(
                Q(driver=user) |
                Q(codriver=user) |
                Q(order_round__transport_coordinator=user) |
                Q(order_round__distribution_coordinator=user)
            )

        rides = rides.order_by("order_round__collect_datetime", "route")

        if (user.groups.filter(name='Admin').exists()):
            return rides
        else:
            return rides.filter(
                order_round__collect_datetime__gte=datetime.date.today()
            )


class Ride(LoginRequiredMixin, UserIsInvolvedMixin, DetailView):
    template_name = "transport/ride.html"
    model = models.Ride


class Cars(LoginRequiredMixin, ListView):
    queryset = VokoUser.objects.filter(
        is_active=True,
        userprofile__shares_car__exact=True
    )
    template_name = "transport/cars.html"
