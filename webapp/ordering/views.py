from django.views.generic import ListView
from ordering.models import Product


class ProductsView(ListView):
    model = Product
