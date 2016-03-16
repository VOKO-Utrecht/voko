from braces.views import LoginRequiredMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.views.generic import ListView, DetailView

from docs.models import Document


class DocumentOverview(LoginRequiredMixin, ListView):
    template_name = 'docs/document_overview.html'
    queryset = Document.objects.all().order_by("-id")


class DocumentDownload(LoginRequiredMixin, DetailView):
    model = Document

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated():
            if self.raise_exception:
                raise PermissionDenied  # return a forbidden response
            else:
                return redirect_to_login(request.get_full_path(),
                                         self.get_login_url(),
                                         self.get_redirect_field_name())

        doc = self.get_object()
        filename = doc.file.name.split('/')[-1]
        response = HttpResponse(doc.file, content_type='application/octet-stream')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename

        return response