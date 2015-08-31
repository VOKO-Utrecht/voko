# -*- coding: utf-8 -*-
import json
import openpyxl
import re
from collections import defaultdict
from tempfile import NamedTemporaryFile
from braces.views import StaffuserRequiredMixin, GroupRequiredMixin
from django.contrib import messages
from django.core.urlresolvers import reverse
from django.db.models.aggregates import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.views.generic import ListView, DetailView, TemplateView, View, FormView
import sys
from accounts.models import VokoUser
from .core import get_current_order_round
from .forms import UploadProductListForm
from .models import OrderProduct, Order, OrderRound, Supplier, OrderProductCorrection, Product, DraftProduct, \
    ProductCategory


class OrderAdminMain(StaffuserRequiredMixin, ListView):
    def get_queryset(self):
        return OrderRound.objects.all().order_by('-id')
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
                order_products = product.orderproducts.filter(order__paid=True)
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
                                          order__paid=True)
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
            filter(orderproducts__order__paid=True).\
            filter(order_round=order_round).\
            annotate(amount_sum=Sum('orderproducts__amount'))

    content_type = "text/csv"


class OrderAdminUserOrdersPerProduct(StaffuserRequiredMixin, ListView):
    def get_queryset(self):
        return OrderProduct.objects.filter(product__pk=self.kwargs.get('pk'),
                                           order__paid=True).order_by("order__user")
    template_name = "ordering/admin/productorder.html"


class OrderAdminUserOrders(StaffuserRequiredMixin, ListView):
    template_name = "ordering/admin/user_orders_per_round.html"

    def get_queryset(self):
        order_round = OrderRound.objects.get(pk=self.kwargs.get('pk'))
        return Order.objects.filter(order_round=order_round, paid=True).order_by("user__first_name")


# Bestellingen per product
class OrderAdminUserOrderProductsPerOrderRound(StaffuserRequiredMixin, ListView):
    def get_queryset(self):
        return OrderProduct.objects.select_related().filter(order__order_round_id=self.kwargs.get('pk'), order__paid=True).\
            order_by('product__supplier')

    def get_context_data(self, **kwargs):
        context = super(OrderAdminUserOrderProductsPerOrderRound, self).get_context_data(**kwargs)

        units = {u[0]: None for u in Product.UNITS}

        orderproducts = self.get_queryset()

        for u in units:
            units[u] = {op.product: [] for op in orderproducts.filter(product__unit_of_measurement=u)}
            for product in units[u]:
                for op in orderproducts.filter(product=product):
                        units[u][product].append(op)


        context['data'] = units

        return context

    template_name = "ordering/admin/productsorders.html"


class OrderAdminCorrectionJson(StaffuserRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        return HttpResponse(
            self.orders_json(),
            content_type="application/json"
        )

    def orders_json(self):
        order_round = OrderRound.objects.get(pk=self.kwargs.get('pk'))
        data = []
        users = set([o.user for o in order_round.orders.all()])

        for user in users:
            orders = []
            for order in user.orders.filter(order_round=order_round, paid=True).select_related():
                order_products = []
                for order_product in order.orderproducts.filter(correction__isnull=True):
                    order_products.append({
                        "id": order_product.id,
                        "name": "%s (%s)" % (order_product.product.name, order_product.product.supplier.name),
                        "amount": order_product.amount
                    })

                if not order_products:
                    continue

                orders.append({
                    "id": order.id,
                    "total_price": float(order.total_price),
                    "order_products": order_products
                })

            if not orders:
                continue

            data.append({
                "name": user.get_full_name(),
                "id": user.id,
                "orders": orders
            })

        return json.dumps(data)


class OrderAdminCorrection(StaffuserRequiredMixin, TemplateView):
    template_name = "ordering/admin/correction.html"

    def post(self, request, *args, **kwargs):
        user_id = int(request.POST['member_id'])
        order_id = int(request.POST['order_id'])
        order_product_id = int(request.POST['order_product_id'])
        supplied_percentage = int(request.POST['supplied_percentage'])
        notes = str((request.POST['notes']).strip())

        order_product = OrderProduct.objects.get(id=order_product_id,
                                                 order_id=order_id,
                                                 order__user_id=user_id)

        OrderProductCorrection.objects.create(
            order_product=order_product,
            supplied_percentage=supplied_percentage,
            notes=notes
        )

        messages.add_message(request, messages.SUCCESS, "De correctie is succesvol aangemaakt.")

        return redirect(reverse('orderadmin_correction', args=args, kwargs=kwargs))

    def corrections(self):
        order_round = OrderRound.objects.get(pk=self.kwargs.get('pk'))
        return OrderProductCorrection.objects.filter(order_product__product__order_round=order_round).order_by("order_product__order__user")

    def products(self):
        order_round = OrderRound.objects.get(pk=self.kwargs.get('pk'))
        return order_round.products.all().order_by('name')


class OrderAdminMassCorrection(StaffuserRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        order_round = OrderRound.objects.get(pk=self.kwargs.get('pk'))
        product_id = request.POST['product_id']
        product = Product.objects.get(order_round=order_round,
                                      id=product_id)
        product.create_corrections()

        messages.add_message(request, messages.SUCCESS, "De correcties zijn succesvol aangemaakt.")

        return redirect(reverse('orderadmin_correction', args=args, kwargs=kwargs))


class ProductAdminMixin(GroupRequiredMixin):
    def _convert_price(self, price):
        if type(price) is unicode:
            price = price.lstrip(u'\u20ac')  # Strip off euro sign
        else:
            price = unicode(str(price), 'utf-8')
        price = price.strip()
        # price = price.replace(".", ",")
        return price

    @property
    def supplier(self):
        return Supplier.objects.get(id=self.kwargs['supplier'])

    @property
    def current_order_round(self):
        return get_current_order_round()

    group_required = 'Boeren'


class UploadProductList(FormView, ProductAdminMixin):
    """
    Used for parsing the form, not displaying anything
    """

    form_class = UploadProductListForm

    def get(self, request, *args, **kwargs):
        return HttpResponseRedirect(reverse('create_draft_products', args=args, kwargs=kwargs))

    def form_valid(self, form):
        try:
            self.create_draft_products_from_spreadsheet(self.request.FILES['product_list'])
        except Exception as e:
            messages.add_message(self.request, messages.ERROR, "Bestand kon niet worden ingelezen. Error: %s" % e)

        return redirect(reverse('create_draft_products', kwargs=self.kwargs))

    def create_draft_products_from_spreadsheet(self, file_handler):
        f = NamedTemporaryFile(delete=False)
        f.write(file_handler.read())
        f.close()

        workbook = openpyxl.load_workbook(f.name, read_only=True)
        sheet = workbook.get_active_sheet()
        PRODUCT_NAME, DESCRIPTION, UNIT, PRICE, MAX, CATEGORY = range(0, 6)

        for idx, row in enumerate(sheet.rows):
            name, description, unit, price, maximum, category = (row[PRODUCT_NAME].value,
                                                                 row[DESCRIPTION].value,
                                                                 row[UNIT].value,
                                                                 row[PRICE].value,
                                                                 row[MAX].value,
                                                                 row[CATEGORY].value)

            if not name or idx == 0:
                continue  # skips header and empty rows

            self._create_draft_product(
                {'name': name,
                 'description': description if description else "",
                 'unit_of_measurement': unit,
                 'base_price': self._convert_price(price),
                 'maximum_total_order': maximum,
                 'category': category}
            )

    def _create_draft_product(self, data):
        return DraftProduct.objects.create(
            supplier=self.supplier,
            order_round=self.current_order_round,
            data=data
        )


class CreateDraftProducts(TemplateView, ProductAdminMixin):
    template_name = "ordering/admin/create_draft_products.html"

    def upload_form(self):
        return UploadProductListForm()

    def draft_products(self):
        for dp in DraftProduct.objects.filter(order_round=self.current_order_round,
                                              supplier=self.supplier).order_by('is_valid', 'id'):
            dp.validate()
            yield dp

    def unit_choices(self):
        return Product.UNITS

    def category_choices(self):
        return [pc.name for pc in ProductCategory.objects.all()]

    def _parse_draft_product_post_data(self):
        """
        yields (product_index, field, data)
        """
        for key in self.request.POST:
            try:
                regex_match = re.match("^product_([a-z_]+)_(\d+)$", key)
                if not regex_match:
                    continue

                field, index = regex_match.groups()
                index = int(index)
                data = unicode(self.request.POST[key])

                print index, field, data
                sys.stdout.flush()

                if not data:
                    data = None
                elif data.isdigit():
                    data = int(data)

                if index == 0:  # the first (hidden) row
                    continue

                yield index, field, data

            except ValueError as e:
                print e
                sys.stdout.flush()
                pass  # other POST value

    def _generate_data_dict_for_draft_products(self):
        tmp = defaultdict(dict)
        for index, field, data in self._parse_draft_product_post_data():
            tmp[index][field] = data

        for index in tmp:
            yield tmp[index]

    def create_draft_products(self):
        for data in self._generate_data_dict_for_draft_products():
            DraftProduct.objects.create(
                supplier=self.supplier,
                order_round=self.current_order_round,
                data=data
            )

    def post(self, *args, **kwargs):
        old_draft_products = DraftProduct.objects.filter(order_round=self.current_order_round,
                                                         supplier=self.supplier)
        old_draft_products.delete()
        self.create_draft_products()

        return redirect(reverse('create_draft_products', kwargs=self.kwargs))


class CreateRealProducts(TemplateView, ProductAdminMixin):
    template_name = "ordering/admin/create_products.html"

    def get(self, *args, **kwargs):
        self.create_products()
        return super(CreateRealProducts, self).get(*args, **kwargs)

    def create_products(self):
        for dp in DraftProduct.objects.filter(supplier=self.supplier,
                                              order_round=self.current_order_round):
            prod = dp.create_product()
            dp.delete()
            prod.determine_if_product_is_new_and_set_label()


class ProductAdminMain(StaffuserRequiredMixin, ListView):
    def get_context_data(self, **kwargs):
        ctx = super(ProductAdminMain, self).get_context_data()
        ctx['current_order_round'] = get_current_order_round()
        return ctx

    def get_queryset(self):
        return Supplier.objects.all().order_by("id")
    template_name = "ordering/admin/suppliers.html"


class RedirectToMailingView(StaffuserRequiredMixin, DetailView):
    model = OrderRound

    def get(self, request, *args, **kwargs):
        queryset = []
        mailing_id = None

        def _user_has_no_orders_in_current_round(voko_user):
            current_order_round = get_current_order_round()
            return not Order.objects.filter(order_round=current_order_round,
                                            user=voko_user, paid=True).exists()

        if kwargs['mailing_type'] == "round-open":
            mailing_id = 11  # Order round open
            queryset = VokoUser.objects.filter(can_activate=True)

        elif kwargs['mailing_type'] == "reminder":
            mailing_id = 4  # Order reminder
            queryset = filter(_user_has_no_orders_in_current_round, VokoUser.objects.filter(is_active=True))

        user_ids = [user.pk for user in queryset]
        request.session['mailing_user_ids'] = user_ids

        return HttpResponseRedirect(reverse("admin_preview_mail", args=(mailing_id,)))
