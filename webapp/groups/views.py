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
    
    def _get_groups(groups_to_show):
        group_ids = []
        for name in groups_to_show:
            id = getattr(config, name)
            group_ids.append(id)
        return Group.objects.filter(pk__in=group_ids)
    
    def _get_members_wo_group():
        return VokoUser.objects.filter(is_active=True,groups__id__isnull=True)
       
    groups = _get_groups(groups_to_show)
   
    queryset = []
    for group in groups:
        members = VokoUser.objects.filter(is_active=True,groups__id=group.id)  
        my_group = {"group": group, "members": members}
        queryset.append(my_group)
        
    queryset.append({"group":Group(name="Leden zonder groep"),"members":_get_members_wo_group})
    
    template_name = "groups/members.html"
    

