from django.views.generic import ListView, DetailView
from ordering.core import get_current_order_round
from ordering.models import Product


class ProductsView(ListView):
    queryset = Product.objects.filter(order_round=get_current_order_round())


class ProductView(DetailView):
    model = Product