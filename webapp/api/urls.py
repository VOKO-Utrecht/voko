from django.conf.urls import url
from api import views

urlpatterns = (
    url(r'^orders(.json)?$', views.OrdersJSONView.as_view()),
    url(r'^orders.csv$', views.OrdersCSVView.as_view()),

    url(r'^accounts(.json)?$', views.AccountsJSONView.as_view()),
    url(r'^accounts.csv$', views.AccountsCSVView.as_view()),
)
