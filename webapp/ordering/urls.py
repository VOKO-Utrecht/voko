from django.conf.urls import patterns, url
from .views import ProductsView, ProductDetail, OrderDisplay, FinishOrder, OrdersDisplay

urlpatterns = patterns('',
    url(r'^products/$', ProductsView.as_view()),
    url(r'^product/(?P<pk>[0-9]+)/$', ProductDetail.as_view()),
    url(r'^order/(?P<pk>[0-9]+)/$', OrderDisplay.as_view(), name="view_order"),
    url(r'^order/(?P<pk>[0-9]+)/finish/$', FinishOrder.as_view(), name="finish_order"),
    url(r'^orders/$', OrdersDisplay.as_view(), name="view_orders"),
)