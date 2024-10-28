from django.urls import path
from ordering import views

urlpatterns = (
    path('supplier/<pk>/', views.SupplierView.as_view(),
         name="view_supplier"),
    path('products/', views.ProductsView.as_view(),
         name="view_products"),
    path('product/<pk>/', views.ProductDetail.as_view(),
         name="view_product"),
    path('order/<pk>/finish/', views.FinishOrder.as_view(),
         name="finish_order"),
    path('order/<pk>/summary/', views.OrderSummary.as_view(),
         name="order_summary"),
    path('orders/', views.OrdersDisplay.as_view(), name="view_orders"),
)
