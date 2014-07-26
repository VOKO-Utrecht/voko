from django.views.generic import ListView
from ordering.core import get_current_order_round
from ordering.models import Product


class ProductsView(ListView):
    queryset = Product.objects.filter(order_round=get_current_order_round())