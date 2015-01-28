from braces.views import LoginRequiredMixin
from django.contrib import messages
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

    def post(self, request, *args, **kwargs):
        """
        Handling complex forms using Django's forms framework is pretty nearly impossible without
         all kinds of trickery that don't necessarily make the code more readable. Hence: manual parsing of POST data.
        """
        order = get_or_create_order(self.request.user)

        for key, value in request.POST.iteritems():
            if key.startswith("order-product-") and (value.isdigit() or value == ""):
                try:
                    prod_id = int(key.split("-")[-1])
                    value = value.strip()
                except (IndexError, ValueError):
                    messages.add_message(self.request, messages.ERROR,
                                         "Er ging iets fout bij het opslaan. "
                                         "Probeer het opnieuw of neem contact met ons op.")
                    return redirect('view_products')

                product = Product.objects.get(id=prod_id)
                try:
                    order_product = OrderProduct.objects.get(order=order, product=product)
                except OrderProduct.DoesNotExist:
                    order_product = None

                if value.isdigit() and product.maximum_total_order and int(value) > product.amount_available:
                    if product.is_available:
                        messages.add_message(self.request, messages.ERROR,
                                             "Van het product %s van %s is nog %s x %s beschikbaar!"
                                             % (product.name, product.supplier.name, product.amount_available,
                                                product.unit_of_measurement))
                    else:
                        messages.add_message(self.request, messages.ERROR, "Het product %s van %s is uitverkocht!"
                                             % (product.name, product.supplier.name))
                    value = 0

                # User deleted a product
                if not value:
                    if order_product:
                        order_product.delete()
                    continue

                # Update orderproduct
                if order_product:
                    if order_product.amount != int(value):
                        order_product.amount = int(value)
                        order_product.save()

                    continue

                # Create orderproduct
                if value and int(value) > 0:
                    OrderProduct.objects.create(order=order, product=product, amount=int(value))

        return redirect('view_products')

    def get_context_data(self, **kwargs):
        context = super(ProductsView, self).get_context_data(**kwargs)
        context['current_order_round'] = self.request.current_order_round
        context['order'] = get_or_create_order(self.request.user)
        return context

    def order_products(self):
        order = get_or_create_order(self.request.user)
        return order.orderproducts.all().select_related()

    def products(self):
        order = get_or_create_order(self.request.user)
        qs = self.get_queryset()
        for prod in qs:
            if prod.orderproducts.filter(order=order):
                prod.ordered_amount = prod.orderproducts.get(order=order).amount
        return qs


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
    ## TODO: Remove this view, as it has become redundant.
    ## It is still used to link to from the user overview. We need a replacement for that.
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

