from django.conf.urls import url
from django.views.generic import RedirectView
from finance import views, admin_views

urlpatterns = (
    url(r'^pay/choosebank/$',
        views.ChooseBankView.as_view(),
        name="finance.choosebank"),
    url(r'^pay/cancel/$',
        views.CancelPaymentView.as_view(),
        name="finance.cancelpayment"),
    url(r'^pay/transaction/create/$',
        views.CreateTransactionView.as_view(),
        name="finance.createtransaction"),
    url(r'^pay/transaction/confirm/$',
        views.ConfirmTransactionView.as_view(),
        name="finance.confirmtransaction"),
    url(r'^pay/transaction/callback/$',
        views.PaymentWebHook.as_view(),
        name="finance.callback"),


    # Admin views
    url(r'^admin/(?P<year>[0-9]+)/specified/$',
        RedirectView.as_view(pattern_name='finance.admin.year.overview',
                             permanent=True)),
    url(r'^admin/json/round/(?P<round_id>[0-9]+)/$',
        admin_views.JsonRoundOverview.as_view(),
        name="finance.admin.round.overview.json"),
    url(r'^admin/round/(?P<round_id>[0-9]+)/$',
        admin_views.RoundOverview.as_view(),
        name="finance.admin.round.overview"),
    url(r'^admin/year/(?P<year>[0-9]+)/$',
        admin_views.YearOverview.as_view(),
        name="finance.admin.year.overview"),
)
