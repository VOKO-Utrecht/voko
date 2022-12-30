from braces.views import LoginRequiredMixin
from django.views.generic import (DetailView, ListView, FormView)
from transport import models
from django.db.models import Q
from accounts.models import VokoUser
from django.contrib.auth.models import Group
from transport.forms import GroupManagerForm
from constance import config


class Members(LoginRequiredMixin, ListView):
    groups_to_show = {'ADMIN_GROUP', 
              'TRANSPORT_GROUP',
              'DISTRIBUTION_GROUP',
              'FARMERS_GROUP',
              'IT_GROUP',
              'PROMO_GROUP'} 
    
    def _get_groups(self):
        group_ids = []
        for name in self.groups_to_show:
            id = getattr(config, name)
            group_ids.append(id)
        return Group.objects.filter(pk__in=group_ids)
    
    def _get_members_wo_group():
        return VokoUser.objects.filter(is_active=True,groups__id__isnull=True).order_by("first_name", "last_name")
    
    def get_queryset(self):
               
        groups = self._get_groups()
   
        queryset = []
        for group in groups:
            members = VokoUser.objects.filter(is_active=True,groups__id=group.id).order_by("first_name", "last_name")  
            my_group = {"group": group, "members": members}
            queryset.append(my_group)
            
        queryset.append({"group":Group(name="Leden zonder groep"),"members":self._get_members_wo_group})
        return queryset

    
    template_name = "groups/members.html"
    
    

