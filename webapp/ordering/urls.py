from django.conf.urls import patterns, url
from .views import ProductsView, ProductDetail, OrderDisplay, FinishOrder, OrdersDisplay, PayOrder, OrderSummary, \
    OrderAdminMain, OrderAdminOrderLists, OrderAdminUserOrdersPerProduct, OrderAdminUserOrders, \
    OrderAdminSupplierOrderCSV, OrderAdminUserOrderProductsPerOrderRound

urlpatterns = patterns('',
    url(r'^products/$', ProductsView.as_view(), name="view_products"),
    url(r'^product/(?P<pk>[0-9]+)/$', ProductDetail.as_view(), name="view_product"),
    url(r'^order/(?P<pk>[0-9]+)/$', OrderDisplay.as_view(), name="view_order"),
    url(r'^order/(?P<pk>[0-9]+)/finish/$', FinishOrder.as_view(), name="finish_order"),
    url(r'^order/(?P<pk>[0-9]+)/pay/$', PayOrder.as_view(), name="pay_order"),
    url(r'^order/(?P<pk>[0-9]+)/summary/$', OrderSummary.as_view(), name="order_summary"),
    url(r'^orders/$', OrdersDisplay.as_view(), name="view_orders"),
    url(r'^admin/$', OrderAdminMain.as_view(), name="orderadmin_main"),
    url(r'^admin/round/(?P<pk>[0-9]+)/order_lists/$', OrderAdminOrderLists.as_view(), name="orderadmin_orderlists"),
    url(r'^admin/round/(?P<pk>[0-9]+)/order_lists/(?P<supplier_pk>[0-9]+).csv', OrderAdminSupplierOrderCSV.as_view(), name="orderadmin_supplier_order_csv"),
    url(r'^admin/round/(?P<pk>[0-9]+)/user_orders/$', OrderAdminUserOrders.as_view(), name="orderadmin_userorders"),
    url(r'^admin/round/(?P<pk>[0-9]+)/product_orders/$', OrderAdminUserOrderProductsPerOrderRound.as_view(), name="orderadmin_orders_per_product"),
    url(r'^admin/product/(?P<pk>[0-9]+)/$', OrderAdminUserOrdersPerProduct.as_view(), name="productorders_admin"),
)