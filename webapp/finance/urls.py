from django.conf.urls import patterns, url
import views

urlpatterns = patterns('',
    url(r'^pay/choosebank/$', views.ChooseBankView.as_view(), name="finance.choosebank"),
    url(r'^pay/transaction/create/$', views.CreateTransactionView.as_view(), name="finance.createtransaction"),
    url(r'^pay/transaction/confirm/$', views.ConfirmTransactionView.as_view(), name="finance.confirmtransaction"),
)