from django.views.generic import ListView, DetailView
from django.views.generic.edit import FormMixin
from ordering.core import get_current_order_round
from ordering.forms import OrderForm
from ordering.models import Product, Order, OrderRound


class ProductsView(ListView):
    queryset = Product.objects.filter(order_round=get_current_order_round())


class ProductView(FormMixin, DetailView):
    model = Product
    form_class = OrderForm

    def get_initial(self):
        order = Order.objects.get_or_create(finalized=False, defaults={'order_round': OrderRound.objects.order_by('-pk')[0],
                                                                       'user': self.request.user})[0]
        initial = {'product': self.get_object().pk,
                   'order': order.pk}
        return initial

    def get_context_data(self, **kwargs):
        context = super(ProductView, self).get_context_data(**kwargs)
        form_class = self.get_form_class()
        context['form'] = self.get_form(form_class)
        return context

