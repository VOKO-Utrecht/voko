from django.http.response import HttpResponseRedirect
from django.shortcuts import redirect
from django.views.generic import View


class HomeView(View):
    def get(self, *args, **kwargs):
        # return redirect('view_products')
        return HttpResponseRedirect("http://vokoutrecht.nl/")