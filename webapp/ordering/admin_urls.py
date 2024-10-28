from django.urls import path
from .admin_views import OrderAdminMain, OrderAdminOrderLists, \
    OrderAdminUserOrdersPerProduct, OrderAdminUserOrders, \
    OrderAdminSupplierOrderCSV, OrderAdminUserOrderProductsPerOrderRound, \
    OrderAdminCorrection, OrderAccounts, OrderAdminMassCorrection, \
    OrderAdminCorrectionJson, UploadProductList, CreateDraftProducts, \
    CreateRealProducts, ProductAdminMain, \
    RedirectToMailingView, StockAdminView, ProductStockApiView, ProductApiView

urlpatterns = (
    path('rounds/', OrderAdminMain.as_view(), name="orderadmin_main"),
    path('suppliers/', ProductAdminMain.as_view(), name="productadmin_main"),
    path('stock/', StockAdminView.as_view(), name="stockadmin_main"),

    path('api/productstock/',
         ProductStockApiView.as_view(),
         name="ordering.api.productstock"),
    path('api/product/',
         ProductApiView.as_view(),
         name="ordering.api.product"),

    path('round/<pk>/order_lists/',
         OrderAdminOrderLists.as_view(),
         name="orderadmin_orderlists"),
    path('round/<pk>/order_lists/<supplier_pk>.csv',
         OrderAdminSupplierOrderCSV.as_view(),
         name="orderadmin_supplier_order_csv"),
    path('round/<pk>/user_orders/',
         OrderAdminUserOrders.as_view(),
         name="orderadmin_userorders"),
    path('round/<pk>/product_orders/',
         OrderAdminUserOrderProductsPerOrderRound.as_view(),
         name="orderadmin_orders_per_product"),
    path('round/<pk>/correction/json',
         OrderAdminCorrectionJson.as_view(),
         name="orderadmin_correction_json"),
    path('round/<pk>/correction/mass',
         OrderAdminMassCorrection.as_view(),
         name="orderadmin_mass_correction"),
    path('round/<pk>/correction/',
         OrderAdminCorrection.as_view(),
         name="orderadmin_correction"),
    path('round/<pk>/accounts/',
         OrderAccounts.as_view(),
         name="orderadmin_accounts"),
    path('round/<pk>/mailing/<mailing_type>round-open/',
         RedirectToMailingView.as_view(), name="productadmin_mailing"),
    path('product/<pk>/',
         OrderAdminUserOrdersPerProduct.as_view(),
         name="productorders_admin"),

    path('supplier/<supplier>/', CreateDraftProducts.as_view(),
         name="create_draft_products"),
    path('supplier/<supplier>/upload/',
         UploadProductList.as_view(), name="upload_products"),
    path('supplier/<supplier>/finish/',
         CreateRealProducts.as_view(), name="create_real_products"),
)
