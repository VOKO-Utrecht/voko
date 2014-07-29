from django.views.generic import ListView, DetailView, FormView, View
from django.views.generic.detail import SingleObjectMixin
from ordering.core import get_current_order_round, get_or_create_order
from ordering.forms import OrderForm
from ordering.models import Product, OrderProduct


class ProductsView(ListView):
    queryset = Product.objects.filter(order_round=get_current_order_round())


class ProductDetail(View):
    def get(self, request, *args, **kwargs):
        view = ProductDisplay.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = ProductOrder.as_view()
        return view(request, *args, **kwargs)


class ProductDisplay(DetailView):
    model = Product

    def _get_initial(self):
        order = get_or_create_order(self.request.user)
        return {'product': self.get_object().pk,
                'order': order.pk}

    def get_context_data(self, **kwargs):
        context = super(ProductDisplay, self).get_context_data(**kwargs)
        context['form'] = OrderForm(initial=self._get_initial())
        return context


class ProductOrder(SingleObjectMixin, FormView):
    model = OrderProduct
    form_class = OrderForm
    success_url = "/hoera"

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = form_class(request.POST)
        print form
        print form.is_valid()
        if form.is_valid():
            # TODO: restrict orders of 0 amount!
            order_product = form.save(commit=False)
            order_product.order = get_or_create_order(request.user)
            order_product.save()
        return self.form_valid(form)


