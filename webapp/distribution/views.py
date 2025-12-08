from braces.views import LoginRequiredMixin, GroupRequiredMixin
from django.views.generic import DetailView, ListView
from distribution import models
import datetime
from distribution.mixins import UserIsInvolvedWithShiftMixin
from accounts.models import VokoUser
from constance import config
from groups.utils.views import GroupmanagerFormView


class Schedule(LoginRequiredMixin, ListView):
    template_name = "distribution/schedule.html"

    def get_context_data(self, **kwargs):
        context = super(Schedule, self).get_context_data(**kwargs)
        # helper to hide/show ride details
        context["isCoordinator"] = self.request.user.groups.filter(name="Uitdeelcoordinatoren").exists()
        return context

    def get_queryset(self):
        user = self.request.user

        if user.groups.filter(name="Uitdeelcoordinatoren").exists():
            shifts = models.Shift.objects.all()
        else:
            shifts = models.Shift.objects.filter(members__in=[user])

        return shifts.filter(order_round__collect_datetime__gte=datetime.date.today()).order_by(
            "order_round__collect_datetime", "start"
        )


class Shift(LoginRequiredMixin, UserIsInvolvedWithShiftMixin, DetailView):
    template_name = "distribution/shift.html"
    model = models.Shift


class Members(LoginRequiredMixin, GroupRequiredMixin, ListView):
    group_required = ("Uitdeelcoordinatoren", "Uitdeel", "Admin")
    template_name = "distribution/members.html"

    def get_queryset(self):
        return VokoUser.objects.filter(is_active=True, groups__id=config.DISTRIBUTION_GROUP).order_by(
            "first_name", "last_name"
        )


class Groupmanager(LoginRequiredMixin, GroupRequiredMixin, GroupmanagerFormView):
    group_required = ("Uitdeelcoordinatoren", "Admin")
    template_name = "distribution/group_mgr.html"
    success_url = "/distribution/groupmanager"

    def get_group_pk(self):
        return config.DISTRIBUTION_GROUP
