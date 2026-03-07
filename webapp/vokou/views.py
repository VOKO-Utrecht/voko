from django.shortcuts import redirect
from django.views.generic import View, TemplateView


class HomeView(View):
    def get(self, *args, **kwargs):
        return redirect('overview')


class RegulationsView(TemplateView):
    template_name = 'regulations.html'
