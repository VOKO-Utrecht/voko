from datetime import datetime, timedelta
from typing import Any
from braces.views import LoginRequiredMixin
from django.views.generic import TemplateView
import pytz
from django.db.models import Q
from news.models import Newsitem
from django.core.exceptions import ObjectDoesNotExist


class NewsitemsView(LoginRequiredMixin, TemplateView):
    template_name = 'news/newsitem_list.html'

    def get_context_data(self, **kwargs: Any):
        ctx = super(NewsitemsView, self).get_context_data(**kwargs)

        # Show all published news published max 1 year ago. Order by publish date (desc)
        ctx['newsitems'] = Newsitem.objects.filter(Q(publish=True) & Q(publish_date__lte=datetime.now(pytz.utc))
                                                   & Q(publish_date__gt=datetime.now(pytz.utc)
                                                       - timedelta(days=365))).order_by("-publish_date")

        try:
            newsitem = Newsitem.objects.get(pk=kwargs['pk'])
        except (KeyError, ObjectDoesNotExist):
            if ctx['newsitems'].first is not None:
                newsitem = ctx['newsitems'].first

        ctx['newsitem'] = newsitem

        return ctx
