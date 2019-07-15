from django.conf.urls import url
from ordering import views

urlpatterns = (
    url(r'^supplier/(?P<pk>[0-9]+)/$', views.SupplierView.as_view(),
        name="view_supplier"),
    url(r'^products/$', views.ProductsView.as_view(),
        name="view_products"),
    url(r'^product/(?P<pk>[0-9]+)/$', views.ProductDetail.as_view(),
        name="view_product"),
    url(r'^order/(?P<pk>[0-9]+)/finish/$', views.FinishOrder.as_view(),
        name="finish_order"),
    url(r'^order/(?P<pk>[0-9]+)/summary/$', views.OrderSummary.as_view(),
        name="order_summary"),
    url(r'^orders/$', views.OrdersDisplay.as_view(), name="view_orders"),
)
