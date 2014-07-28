from django.conf.urls import patterns, url
from .views import ProductsView, ProductView

urlpatterns = patterns('',
    url(r'^products/', ProductsView.as_view()),
    url(r'^product/(?P<pk>[0-9]+)/$', ProductView.as_view()),
)