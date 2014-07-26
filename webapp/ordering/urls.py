from django.conf.urls import patterns, url
from .views import ProductsView

urlpatterns = patterns('',
    url(r'^products/', ProductsView.as_view()),
)