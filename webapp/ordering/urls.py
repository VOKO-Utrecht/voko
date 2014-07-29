from django.conf.urls import patterns, url
from .views import ProductsView, ProductDisplay, ProductDetail

urlpatterns = patterns('',
    url(r'^products/', ProductsView.as_view()),
    url(r'^product/(?P<pk>[0-9]+)/$', ProductDetail.as_view()),
)