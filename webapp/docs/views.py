from braces.views import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic import ListView, DetailView

from docs.models import Document


class DocumentOverview(LoginRequiredMixin, ListView):
    template_name = 'docs/document_overview.html'
    queryset = Document.objects.all().order_by("-id")


class DocumentDownload(LoginRequiredMixin, DetailView):
    model = Document

    def dispatch(self, request, *args, **kwargs):
        doc = self.get_object()

        filename = doc.file.name.split('/')[-1]
        response = HttpResponse(doc.file, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response