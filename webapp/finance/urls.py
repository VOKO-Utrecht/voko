from django.conf.urls import patterns, url
import views
import admin_views

urlpatterns = patterns('',
    url(r'^pay/choosebank/$', views.ChooseBankView.as_view(), name="finance.choosebank"),
    url(r'^pay/cancel/$', views.CancelPaymentView.as_view(), name="finance.cancelpayment"),
    url(r'^pay/transaction/create/$', views.CreateTransactionView.as_view(), name="finance.createtransaction"),
    url(r'^pay/transaction/confirm/$', views.ConfirmTransactionView.as_view(), name="finance.confirmtransaction"),
    url(r'^pay/transaction/callback/$', views.QantaniCallbackView.as_view(), name="finance.callback"),
    url(r'^admin/(?P<year>[0-9]+)/specified/$', admin_views.RoundsPerYearView.as_view(), name="finance.admin.specified"),

)