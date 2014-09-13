from braces.views import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.forms import inlineformset_factory
from django.http import HttpResponseForbidden, HttpResponseBadRequest
from django.views.generic import ListView, DetailView, FormView, View, UpdateView
from django.views.generic.detail import SingleObjectMixin
from ordering.core import get_current_order_round, get_or_create_order, get_order_product
from ordering.forms import OrderProductForm
from ordering.mixins import UserOwnsObjectMixin
from ordering.models import Product, OrderProduct, Order


class ProductsView(LoginRequiredMixin, ListView):
    queryset = Product.objects.filter(order_round=get_current_order_round())


class ProductDetail(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        view = ProductDisplay.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = ProductOrder.as_view()
        return view(request, *args, **kwargs)


class ProductDisplay(LoginRequiredMixin, DetailView):
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


class ProductOrder(LoginRequiredMixin, SingleObjectMixin, FormView):
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
            order_product = form.save(commit=False)
            order_product.order = get_or_create_order(request.user)
            assert order_product.product.order_round == get_current_order_round()  # TODO: nicer error, or just disable ordering.

            # Remove order when amount is zero
            if order_product.amount < 1:
                if order_product.id is not None:
                    order_product.delete()
                return self.form_valid(form)

            order_product.save()
        return self.form_valid(form)


class OrderDisplay(LoginRequiredMixin, UserOwnsObjectMixin, UpdateView):
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

        if self.object.finalized:
            return HttpResponseBadRequest()

        if fs.is_valid():
            fs.save()
            ## TODO: add 'succeeded' message

        # Errors are saved in formset.errors: TODO: show them in template.
        return self.render_to_response(self.get_context_data(form=self.get_form(self.form_class)))


class FinishOrder(LoginRequiredMixin, UserOwnsObjectMixin, UpdateView):
    template_name = "ordering/order_finish.html"
    model = Order

    def post(self, request, *args, **kwargs):
        order = self.get_object()
        # You cannot finalize a finalized order
        if order.finalized:
            return HttpResponseBadRequest()

        # For now, we just finish the order.
        order.place_order_and_debit()
        order.create_and_add_payment()
        order.finalized = True
        order.save()
        print "HOERA"


class OrdersDisplay(LoginRequiredMixin, UserOwnsObjectMixin, ListView):
    """
    Overview of multiple orders
    """
    def get_queryset(self):
        return self.request.user.orders.all().order_by("-pk")
