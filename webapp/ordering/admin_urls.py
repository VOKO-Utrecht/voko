from django.conf.urls import url
from .admin_views import OrderAdminMain, OrderAdminOrderLists, \
    OrderAdminUserOrdersPerProduct, OrderAdminUserOrders, \
    OrderAdminSupplierOrderCSV, OrderAdminUserOrderProductsPerOrderRound, \
    OrderAdminCorrection, OrderAccounts, OrderAdminMassCorrection, \
    OrderAdminCorrectionJson, UploadProductList, CreateDraftProducts, \
    CreateRealProducts, ProductAdminMain, \
    RedirectToMailingView, StockAdminView, ProductStockApiView, ProductApiView

urlpatterns = (
    url(r'^rounds/$', OrderAdminMain.as_view(), name="orderadmin_main"),
    url(r'^suppliers/$', ProductAdminMain.as_view(), name="productadmin_main"),
    url(r'^stock/$', StockAdminView.as_view(), name="stockadmin_main"),

    url(r'^api/productstock/$', ProductStockApiView.as_view(),
        name="ordering.api.productstock"),
    url(r'^api/product/$', ProductApiView.as_view(),
        name="ordering.api.product"),

    url(r'^round/(?P<pk>[0-9]+)/order_lists/$', OrderAdminOrderLists.as_view(),
        name="orderadmin_orderlists"),
    url(r'^round/(?P<pk>[0-9]+)/order_lists/(?P<supplier_pk>[0-9]+).csv',
        OrderAdminSupplierOrderCSV.as_view(),
        name="orderadmin_supplier_order_csv"),
    url(r'^round/(?P<pk>[0-9]+)/user_orders/$', OrderAdminUserOrders.as_view(),
        name="orderadmin_userorders"),
    url(r'^round/(?P<pk>[0-9]+)/product_orders/$',
        OrderAdminUserOrderProductsPerOrderRound.as_view(),
        name="orderadmin_orders_per_product"),
    url(r'^round/(?P<pk>[0-9]+)/correction/json',
        OrderAdminCorrectionJson.as_view(), name="orderadmin_correction_json"),
    url(r'^round/(?P<pk>[0-9]+)/correction/mass$',
        OrderAdminMassCorrection.as_view(), name="orderadmin_mass_correction"),
    url(r'^round/(?P<pk>[0-9]+)/correction/$', OrderAdminCorrection.as_view(),
        name="orderadmin_correction"),
    url(r'^round/(?P<pk>[0-9]+)/accounts/$', OrderAccounts.as_view(),
        name="orderadmin_accounts"),
    url(r'^round/(?P<pk>[0-9]+)/mailing/(?P<mailing_type>(round-open))/$',
        RedirectToMailingView.as_view(), name="productadmin_mailing"),
    url(r'^product/(?P<pk>[0-9]+)/$', OrderAdminUserOrdersPerProduct.as_view(),
        name="productorders_admin"),

    url(r'^supplier/(?P<supplier>[0-9]+)/$', CreateDraftProducts.as_view(),
        name="create_draft_products"),
    url(r'^supplier/(?P<supplier>[0-9]+)/upload/$',
        UploadProductList.as_view(), name="upload_products"),
    url(r'^supplier/(?P<supplier>[0-9]+)/finish/$',
        CreateRealProducts.as_view(), name="create_real_products"),
)
