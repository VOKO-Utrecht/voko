from django.urls import path, re_path
from api import views

urlpatterns = (
    re_path(r'^orders(.json)?$', views.OrdersJSONView.as_view()),
    path('orders.csv', views.OrdersCSVView.as_view()),

    re_path(r'^accounts(.json)?$', views.AccountsJSONView.as_view()),
    path('accounts.csv', views.AccountsCSVView.as_view()),
)
