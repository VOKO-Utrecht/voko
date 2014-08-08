from django.conf.urls import patterns, url
from .views import ProductsView, ProductDisplay, ProductDetail, OrderDisplay

urlpatterns = patterns('',
    url(r'^products/', ProductsView.as_view()),
    url(r'^product/(?P<pk>[0-9]+)/$', ProductDetail.as_view()),
    url(r'^order/(?P<pk>[0-9]+)/$', OrderDisplay.as_view(), name="view_order"),
)