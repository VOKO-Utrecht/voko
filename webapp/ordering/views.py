from braces.views import LoginRequiredMixin, StaffuserRequiredMixin
from django.core.urlresolvers import reverse
from django.db.models.aggregates import Sum
from django.forms import inlineformset_factory
from django.http import HttpResponseBadRequest
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, FormView, View, UpdateView
from django.views.generic.detail import SingleObjectMixin
from ordering.core import get_or_create_order, get_order_product, \
    update_totals_for_products_with_max_order_amounts
from ordering.forms import OrderProductForm
from ordering.mixins import UserOwnsObjectMixin
from ordering.models import Product, OrderProduct, Order, OrderRound, Supplier


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


### ADMIN VIEWS ###

class OrderAdminMain(StaffuserRequiredMixin, ListView):
    def get_queryset(self):
        return OrderRound.objects.all().order_by('id')
    template_name = "ordering/admin/orderrounds.html"


class OrderAdminOrderLists(StaffuserRequiredMixin, DetailView):
    model = OrderRound
    template_name = "ordering/admin/orderround.html"

    def _get_orders_per_supplier(self):
        data = {}
        order_round = self.get_object()
        for supplier in Supplier.objects.all():
            suppliers_products_this_round = supplier.products.filter(order_round=order_round)
            data[supplier] = {'orderproducts': [],
                              'sum': self._get_total_prices_per_supplier(supplier, order_round)}

            for product in suppliers_products_this_round:
                order_products = product.orderproducts.filter(order__finalized=True)
                product_sum = sum([op.amount for op in order_products])
                if product_sum == 0:
                    continue

                data[supplier]['orderproducts'].append({'product': product,
                                                        'amount': product_sum,
                                                        'sub_total': product_sum * product.base_price})

        return data

    def _get_total_prices_per_supplier(self, supplier, order_round):
        ops = OrderProduct.objects.filter(product__supplier=supplier,
                                          order__order_round=order_round,
                                          order__finalized=True)
        return sum([op.amount * op.product.base_price for op in ops])

    def get_context_data(self, **kwargs):
        context = super(OrderAdminOrderLists, self).get_context_data(**kwargs)
        context['orders_per_supplier'] = self._get_orders_per_supplier()
        return context


class OrderAdminSupplierOrderCSV(StaffuserRequiredMixin, ListView):
    template_name = "ordering/admin/orderlist_per_supplier.html"

    def get_queryset(self):
        supplier = Supplier.objects.get(pk=self.kwargs.get('supplier_pk'))
        order_round = OrderRound.objects.get(pk=self.kwargs.get('pk'))

        return supplier.products.\
            exclude(orderproducts=None).\
            filter(orderproducts__order__finalized=True).\
            filter(order_round=order_round).\
            annotate(amount_sum=Sum('orderproducts__amount'))

    content_type = "text/csv"


class OrderAdminUserOrdersPerProduct(StaffuserRequiredMixin, ListView):
    def get_queryset(self):
        return OrderProduct.objects.filter(product__pk=self.kwargs.get('pk'),
                                           order__finalized=True).order_by("order__user")
    template_name = "ordering/admin/productorder.html"


class OrderAdminUserOrders(StaffuserRequiredMixin, ListView):
    template_name = "ordering/admin/user_orders_per_round.html"

    def get_queryset(self):
        order_round = OrderRound.objects.get(pk=self.kwargs.get('pk'))
        return Order.objects.filter(order_round=order_round, finalized=True).order_by("user")


class OrderAdminUserOrderProductsPerOrderRound(StaffuserRequiredMixin, ListView):
    def get_queryset(self):
        return OrderProduct.objects.select_related().filter(order__order_round_id=self.kwargs.get('pk'), order__finalized=True).\
            order_by('product__supplier').\
            order_by('product')

    def get_context_data(self, **kwargs):
        context = super(OrderAdminUserOrderProductsPerOrderRound, self).get_context_data(**kwargs)

        suppliers = {s: None for s in Supplier.objects.all()}
        orderproducts = self.get_queryset()

        for s in suppliers:
            suppliers[s] = {op.product: [] for op in orderproducts.filter(product__supplier=s)}
            for product in suppliers[s]:
                for op in orderproducts.filter(product=product):
                    suppliers[s][product].append(op)

        context['data'] = suppliers

        return context


    template_name = "ordering/admin/productsorders.html"
