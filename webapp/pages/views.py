from braces.views import LoginRequiredMixin
from django.http import Http404
from django.views.generic import DetailView

from pages.models import Page


class PageDetailView(LoginRequiredMixin, DetailView):
    model = Page
    template_name = "pages/page_detail.html"
    context_object_name = "page"

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if not obj.published:
            raise Http404
        return obj
