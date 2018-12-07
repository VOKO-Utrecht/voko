from django.conf.urls import url
from .views import ProductsView, ProductDetail, FinishOrder, OrdersDisplay, \
    OrderSummary, SupplierView

urlpatterns = (
    url(r'^supplier/(?P<pk>[0-9]+)/$', SupplierView.as_view(),
        name="view_supplier"),
    url(r'^products/$', ProductsView.as_view(), name="view_products"),
    url(r'^product/(?P<pk>[0-9]+)/$', ProductDetail.as_view(),
        name="view_product"),
    url(r'^order/(?P<pk>[0-9]+)/finish/$', FinishOrder.as_view(),
        name="finish_order"),
    url(r'^order/(?P<pk>[0-9]+)/summary/$', OrderSummary.as_view(),
        name="order_summary"),
    url(r'^orders/$', OrdersDisplay.as_view(), name="view_orders"),
)
