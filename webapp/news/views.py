from datetime import datetime, timedelta
from braces.views import LoginRequiredMixin
from django.views.generic import (
    ListView, DetailView
)
from django.shortcuts import render
import pytz
from django.db.models import Q
from news.models import Newsitem


class NewsitemsView(LoginRequiredMixin, ListView):
    template_name = 'news/newsitem_list.html'

    def get_queryset(self):
        return Newsitem.objects.filter(Q(publish=True) & Q(publish_date__lte=datetime.now(pytz.utc))
            & Q(publish_date__gt=datetime.now(pytz.utc) - timedelta(days=60))).order_by("-publish_date")
    
class NewsitemDetail(LoginRequiredMixin, DetailView):
    template_name = 'news/newsitem_detail.html'
    model = Newsitem
