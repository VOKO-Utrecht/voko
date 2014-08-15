from django.core.urlresolvers import reverse
from django.forms import inlineformset_factory
from django.views.generic import ListView, DetailView, FormView, View, UpdateView
from django.views.generic.detail import SingleObjectMixin
from ordering.core import get_current_order_round, get_or_create_order, get_order_product
from ordering.forms import OrderProductForm
from ordering.models import Product, OrderProduct, Order


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

        existing_op = get_order_product(product=self.get_object(),
                                        order=get_or_create_order(self.request.user))
        context['form'] = OrderProductForm(initial=self._get_initial(), instance=existing_op)
        return context


class ProductOrder(SingleObjectMixin, FormView):
    model = Product
    form_class = OrderProductForm

    def get_success_url(self):
        return reverse("view_order", kwargs={'pk': get_or_create_order(self.request.user).pk})

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = form_class(request.POST, instance=get_order_product(product=self.get_object(),
                                                                   order=get_or_create_order(
                                                                       user=self.request.user
                                                                   )))
        if form.is_valid():
            # TODO: restrict orders of 0 amount!
            order_product = form.save(commit=False)
            order_product.order = get_or_create_order(request.user)
            order_product.save()
            print order_product.pk
        return self.form_valid(form)


class OrderDisplay(UpdateView):
    # TODO: restrict to user only
    model = Order
    form_class = OrderProductForm
    success_url = "/hoera"

    def get_context_data(self, **kwargs):
        context = super(OrderDisplay, self).get_context_data(**kwargs)
        FormSet = inlineformset_factory(self.model, OrderProduct, extra=0, form=self.form_class)
        fs = FormSet(instance=self.get_object())
        context['formset'] = fs
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        FormSet = inlineformset_factory(self.model, OrderProduct, extra=0, form=self.form_class)
        fs = FormSet(instance=self.get_object(), data=request.POST)
        if fs.is_valid():
            # TODO: validate if form may be modified still (isn't it finished?)
            fs.save()
            ## TODO: add 'succeeded' message

        # Errors are saved in formset.errors: TODO: show them in template.
        return self.render_to_response(self.get_context_data(form=self.get_form(self.form_class)))


class FinishOrder(UpdateView):
    template_name = "ordering/order_finish.html"
    model = Order

    def post(self, request, *args, **kwargs):
        # For now, we just finish the order.
        order = self.get_object()
        order.place_order_and_debit()
        order.create_and_add_payment()
        order.finalized = True
        order.save()
        print "HOERA"


class OrdersDisplay(ListView):
    """
    Overview of multiple orders
    """
    def get_queryset(self):
        return self.request.user.orders.all().order_by("-pk")
