from braces.views import LoginRequiredMixin
from django.core.urlresolvers import reverse
from django.forms import inlineformset_factory
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, FormView, View, UpdateView
from django.views.generic.detail import SingleObjectMixin
from ordering.core import get_or_create_order, get_order_product, update_totals_for_products_with_max_order_amounts
from ordering.forms import OrderProductForm
from ordering.mixins import UserOwnsObjectMixin
from ordering.models import Product, OrderProduct, Order, Supplier


class ProductsView(LoginRequiredMixin, ListView):
    def get_queryset(self):
        return Product.objects.filter(order_round=self.request.current_order_round).order_by('name')

    def get_context_data(self, **kwargs):
        context = super(ProductsView, self).get_context_data(**kwargs)
        context['current_order_round'] = self.request.current_order_round
        return context


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

    def form(self):
        existing_op = get_order_product(product=self.get_object(),
                                        order=get_or_create_order(self.request.user))
        return OrderProductForm(initial=self._get_initial(), instance=existing_op)


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
            assert order_product.product.order_round == self.request.current_order_round  # TODO: nicer error, or just disable ordering.

            # Remove product from order when amount is zero
            if order_product.amount < 1:
                if order_product.id is not None:
                    order_product.delete()
                return self.form_valid(form)

            order_product.save()
        return self.form_valid(form)


class OrderDisplay(LoginRequiredMixin, UserOwnsObjectMixin, UpdateView):
    model = Order
    form_class = OrderProductForm
    success_url = "/hoera"

    def formset(self):
        update_totals_for_products_with_max_order_amounts(self.get_object())
        FormSet = inlineformset_factory(self.model, OrderProduct, extra=0, form=self.form_class)
        return FormSet(instance=self.get_object())

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

    def get_queryset(self):
        qs = super(FinishOrder, self).get_queryset()
        return qs.filter(finalized=False)

    def get_context_data(self, **kwargs):
        update_totals_for_products_with_max_order_amounts(self.get_object())
        return super(UpdateView, self).get_context_data(**kwargs)

    def post(self, request, *args, **kwargs):
        order = self.get_object()
        if order.debit:
            order.update_debit()
        else:
            order.create_and_link_debit()
        order.save()
        return redirect('finance.choosebank')


class OrdersDisplay(LoginRequiredMixin, UserOwnsObjectMixin, ListView):
    """
    Overview of multiple orders
    """
    def get_queryset(self):
        return self.request.user.orders.all().order_by("-pk")


class OrderSummary(LoginRequiredMixin, UserOwnsObjectMixin, UpdateView):
    template_name = "ordering/order_summary.html"
    model = Order

    def get_queryset(self):
        qs = super(OrderSummary, self).get_queryset()
        return qs.filter(finalized=True)


class SupplierView(LoginRequiredMixin, DetailView):
    model = Supplier

