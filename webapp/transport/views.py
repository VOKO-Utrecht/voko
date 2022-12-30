from braces.views import LoginRequiredMixin
from django.views.generic import (DetailView, ListView, FormView)
from transport import models
from django.db.models import Q
import datetime
from transport.mixins import UserIsInvolvedMixin, IsTransportCoordinatorMixin, IsInTransportMixin
from accounts.models import VokoUser
from django.contrib.auth.models import Group
from transport.forms import GroupManagerForm
from constance import config


class Schedule(LoginRequiredMixin, ListView):
    template_name = "transport/schedule.html"

    def get_queryset(self):
        user = self.request.user

        if (user.groups.filter(
            name__in=['Transportcoordinatoren', 'Admin']
        ).exists()):
            rides = models.Ride.objects.all()
        else:
            rides = models.Ride.objects.filter(
                Q(driver=user)
                | Q(codriver=user)
                | Q(order_round__transport_coordinator=user)
                | Q(order_round__distribution_coordinator=user)
            )

        rides = rides.order_by("-order_round__collect_datetime", "route")

        if (user.groups.filter(name='Admin').exists()):
            return rides
        else:
            return rides.filter(
                order_round__collect_datetime__gte=datetime.date.today()
            )


class Ride(LoginRequiredMixin, UserIsInvolvedMixin, DetailView):
    template_name = "transport/ride.html"
    model = models.Ride


class Cars(LoginRequiredMixin, IsInTransportMixin, ListView):
    queryset = VokoUser.objects.filter(
        is_active=True,
        userprofile__shares_car__exact=True
    )
    template_name = "transport/cars.html"


class Members(LoginRequiredMixin, IsInTransportMixin, ListView):
    queryset = VokoUser.objects.filter(
        is_active=True,
        groups__id=config.TRANSPORT_GROUP).order_by("first_name", "last_name")  
    template_name = "transport/members.html"


class Groupmanager(LoginRequiredMixin, IsTransportCoordinatorMixin, FormView):

    template_name = "transport/group_mgr.html"
    form_class = GroupManagerForm
    model = Group
    success_url = "/transport/groupmanager"

    def post(self, request, *args, **kwargs):
        transport_group = Group.objects.get(pk=config.TRANSPORT_GROUP)
        form = GroupManagerForm(request.POST)
        if (form.is_valid()):
            if "cancel" in request.POST:
                return self.success_url
            else:
                user_ids = request.POST.getlist('users', [])
                self._update_groupmembers(transport_group, user_ids)
        return super().form_valid(form)

    def _update_groupmembers(self, group, members_ids):

        members = VokoUser.objects.all().filter(pk__in=members_ids)
        members_to_add = []
        members_to_remove = []
        for m in members:
            if (group.user_set.all().filter(id=m.id).first() is None):
                # members_to_add.append(m)
                m.groups.add(group)

        members_ids = [int(item) for item in members_ids]
        for m in group.user_set.all():
            if (m.id not in members_ids):
                # members_to_remove.append(m)
                m.groups.remove(group)
 
        # group.user_set.add(*members_to_add)
        # group.user_set.remove(*members_to_remove)
