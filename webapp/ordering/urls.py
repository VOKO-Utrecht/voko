from django.urls import path
from ordering import views

urlpatterns = (
    path("supplier/<int:pk>/", views.SupplierView.as_view(), name="view_supplier"),
    path("products/", views.ProductsView.as_view(), name="view_products"),
    path("product/<int:pk>/", views.ProductDetail.as_view(), name="view_product"),
    path("order/<int:pk>/finish/", views.FinishOrder.as_view(), name="finish_order"),
    path("order/<int:pk>/summary/", views.OrderSummary.as_view(), name="order_summary"),
    path("orders/", views.OrdersDisplay.as_view(), name="view_orders"),
)
