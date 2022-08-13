from braces.views import LoginRequiredMixin
from django.views.generic import (DetailView, ListView)
from distribution import models
import datetime
from distribution.mixins import UserIsInvolvedWithShiftMixin


class Schedule(LoginRequiredMixin, ListView):
    template_name = "distribution/schedule.html"

    def get_context_data(self, **kwargs):
        context = super(Schedule, self).get_context_data(**kwargs)
        # helper to hide/show ride details
        context['isCoordinator'] = self.request.user.groups.filter(name='Uitdeelcoordinatoren').exists()
        return context

    def get_queryset(self):
        user = self.request.user

        if (user.groups.filter(name='Uitdeelcoordinatoren').exists()):
            shifts = models.Shift.objects.all()
        else:
            shifts = models.Shift.objects.filter(members__in=[user])

        return shifts.filter(
            order_round__collect_datetime__gte=datetime.date.today()
        ).order_by("order_round__collect_datetime", "start")


class Shift(LoginRequiredMixin, UserIsInvolvedWithShiftMixin, DetailView):
    template_name = "distribution/shift.html"
    model = models.Shift
