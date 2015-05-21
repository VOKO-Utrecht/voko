from django.conf.urls import patterns, url
from .admin_views import OrderAdminMain, OrderAdminOrderLists, OrderAdminUserOrdersPerProduct, OrderAdminUserOrders, \
    OrderAdminSupplierOrderCSV, OrderAdminUserOrderProductsPerOrderRound, OrderAdminCorrection, OrderAdminMassCorrection, \
    OrderAdminCorrectionJson, UploadProductList, CreateDraftProducts, CreateRealProducts

urlpatterns = patterns('',
    url(r'^$', OrderAdminMain.as_view(), name="orderadmin_main"),
    url(r'^round/(?P<pk>[0-9]+)/order_lists/$', OrderAdminOrderLists.as_view(), name="orderadmin_orderlists"),
    url(r'^round/(?P<pk>[0-9]+)/order_lists/(?P<supplier_pk>[0-9]+).csv', OrderAdminSupplierOrderCSV.as_view(), name="orderadmin_supplier_order_csv"),
    url(r'^round/(?P<pk>[0-9]+)/user_orders/$', OrderAdminUserOrders.as_view(), name="orderadmin_userorders"),
    url(r'^round/(?P<pk>[0-9]+)/product_orders/$', OrderAdminUserOrderProductsPerOrderRound.as_view(), name="orderadmin_orders_per_product"),
    url(r'^round/(?P<pk>[0-9]+)/correction/json', OrderAdminCorrectionJson.as_view(), name="orderadmin_correction_json"),
    url(r'^round/(?P<pk>[0-9]+)/correction/mass$', OrderAdminMassCorrection.as_view(), name="orderadmin_mass_correction"),
    url(r'^round/(?P<pk>[0-9]+)/correction/$', OrderAdminCorrection.as_view(), name="orderadmin_correction"),
    url(r'^product/(?P<pk>[0-9]+)/$', OrderAdminUserOrdersPerProduct.as_view(), name="productorders_admin"),
    url(r'^productadmin/supplier/(?P<supplier>[0-9]+)/upload/$', UploadProductList.as_view(), name="upload_products"),
    url(r'^productadmin/supplier/(?P<supplier>[0-9]+)/$', CreateDraftProducts.as_view(), name="create_draft_products"),
    url(r'^productadmin/supplier/(?P<supplier>[0-9]+)/finish/$', CreateRealProducts.as_view(), name="create_real_products"),
)