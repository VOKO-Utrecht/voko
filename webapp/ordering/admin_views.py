from braces.views import StaffuserRequiredMixin
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models.aggregates import Sum
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, View, UpdateView, TemplateView
from accounts.models import VokoUser
from ordering.models import OrderProduct, Order, OrderRound, Supplier, OrderProductCorrection


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


class OrderAdminCorrection(StaffuserRequiredMixin, TemplateView):
    template_name = "ordering/admin/correction.html"

    # def get_queryset(self):
    #     self.order_round = OrderRound.objects.get(pk=self.kwargs.get('pk'))
    #     return OrderProductCorrection.objects.filter(order_product__product__order_round=self.order_round)

    def post(self, request, *args, **kwargs):
        print request.POST

        messages.add_message(request, messages.SUCCESS, "De correctie is succesvol aangemaakt.")

        return redirect(reverse('orderadmin_correction', args=args, kwargs=kwargs))


class OrderAdminCorrectionJSON(StaffuserRequiredMixin, View):
    """
    JSON data for OrderAdminCorrection view
    """

    def get(self, *args, **kwargs):
        order_round = OrderRound.objects.get(pk=self.kwargs.get('pk'))
        data = []

        # for user in

