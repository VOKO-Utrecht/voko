from django.urls import path
from django.views.generic import RedirectView
from finance import views, admin_views

urlpatterns = (
    path("pay/cancel/", views.CancelPaymentView.as_view(), name="finance.cancelpayment"),
    path("pay/transaction/create/", views.CreateTransactionView.as_view(), name="finance.createtransaction"),
    path("pay/transaction/confirm/", views.ConfirmTransactionView.as_view(), name="finance.confirmtransaction"),
    path("pay/transaction/callback/", views.PaymentWebHook.as_view(), name="finance.callback"),
    # Admin views
    path(
        "admin/<int:year>/specified/", RedirectView.as_view(pattern_name="finance.admin.year.overview", permanent=True)
    ),
    path(
        "admin/json/round/<int:round_id>/",
        admin_views.JsonRoundOverview.as_view(),
        name="finance.admin.round.overview.json",
    ),
    path("admin/round/<int:round_id>/", admin_views.RoundOverview.as_view(), name="finance.admin.round.overview"),
    path("admin/year/<int:year>/", admin_views.YearOverview.as_view(), name="finance.admin.year.overview"),
)
