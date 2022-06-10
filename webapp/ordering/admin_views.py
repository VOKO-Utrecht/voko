# -*- coding: utf-8 -*-
import json
from decimal import Decimal, ROUND_DOWN

import openpyxl
import re
from collections import defaultdict
from tempfile import NamedTemporaryFile
from braces.views import GroupRequiredMixin
from django.contrib import messages
from django.urls import reverse
from django.db import IntegrityError
from django.db.models.aggregates import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.utils.datastructures import MultiValueDictKeyError
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView, DetailView, TemplateView, View, \
    FormView
import sys
from accounts.models import VokoUser
from .core import get_current_order_round
from .forms import UploadProductListForm
from .models import OrderProduct, Order, OrderRound, Supplier, \
    OrderProductCorrection, Product, DraftProduct, \
    ProductCategory, ProductStock, ProductUnit


class OrderAdminMain(GroupRequiredMixin, ListView):
    template_name = "ordering/admin/orderrounds.html"
    group_required = ('Uitdeelcoordinatoren', 'Admin')

    def get_queryset(self):
        return OrderRound.objects.all().order_by('-id')


class OrderAdminOrderLists(GroupRequiredMixin, DetailView):
    model = OrderRound
    template_name = "ordering/admin/orderround.html"
    group_required = ('Uitdeelcoordinatoren', 'Admin', 'Uitdeel')


class OrderAdminSupplierOrderCSV(GroupRequiredMixin, ListView):
    template_name = "ordering/admin/orderlist_per_supplier.html"
    group_required = ('Uitdeelcoordinatoren', 'Admin', 'Boeren')

    def get_queryset(self):
        supplier = Supplier.objects.get(pk=self.kwargs.get('supplier_pk'))
        order_round = OrderRound.objects.get(pk=self.kwargs.get('pk'))

        return supplier.products. \
            exclude(orderproducts=None). \
            filter(orderproducts__order__paid=True). \
            filter(order_round=order_round). \
            annotate(amount_sum=Sum('orderproducts__amount'))

    content_type = "text/csv"


class OrderAdminUserOrdersPerProduct(GroupRequiredMixin, ListView):
    group_required = ('Uitdeelcoordinatoren', 'Admin', 'Boeren')
    template_name = "ordering/admin/productorder.html"

    def get_queryset(self):
        return OrderProduct.objects.filter(product__pk=self.kwargs.get('pk'),
                                           order__paid=True).order_by(
            "order__user")


class OrderAdminUserOrders(GroupRequiredMixin, ListView):
    group_required = ('Uitdeelcoordinatoren', 'Admin', 'Boeren', 'Uitdeel')
    template_name = "ordering/admin/user_orders_per_round.html"

    def get_queryset(self):
        self.order_round = OrderRound.objects.get(pk=self.kwargs.get('pk'))
        return Order.objects.filter(order_round=self.order_round,
                                    paid=True).order_by("user__first_name")

    def get_context_data(self, **kwargs):
        context = super(OrderAdminUserOrders, self).get_context_data(**kwargs)
        context['order_round'] = self.order_round
        return context


# Bestellingen per product
class OrderAdminUserOrderProductsPerOrderRound(GroupRequiredMixin, ListView):
    group_required = ('Uitdeelcoordinatoren', 'Admin', 'Boeren', 'Uitdeel')
    template_name = "ordering/admin/productsorders.html"

    def get_queryset(self):
        self.order_round = OrderRound.objects.get(pk=self.kwargs.get('pk'))
        return OrderProduct.objects.select_related().filter(
            order__order_round_id=self.kwargs.get('pk'), order__paid=True)

    def get_context_data(self, **kwargs):
        context = super(OrderAdminUserOrderProductsPerOrderRound,
                        self).get_context_data(**kwargs)

        # this is one way to nest defaultdicts
        data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        for orderprod in self.get_queryset():
            data[orderprod.product.supplier][orderprod.product.category][
                orderprod.product].append(orderprod)

        # convert to regular dicts so Django templating can handle it
        data = dict(data)
        for k, v in list(data.items()):
            data[k] = dict(v)
            for a, b in list(data[k].items()):
                data[k][a] = dict(b)

        context['data'] = data
        context['order_round'] = self.order_round
        return context


class OrderAdminCorrectionJson(GroupRequiredMixin, View):
    group_required = ('Uitdeelcoordinatoren', 'Admin')

    def get(self, request, *args, **kwargs):
        return HttpResponse(
            self.orders_json(),
            content_type="application/json"
        )

    def orders_json(self):
        order_round = OrderRound.objects.get(pk=self.kwargs.get('pk'))
        data = []
        users = set([o.user for o in order_round.orders.all()])
        users = sorted(users, key=lambda x: x.first_name)

        for user in users:
            orders = []
            for order in user.orders.filter(order_round=order_round,
                                            paid=True).select_related():
                order_products = []
                for order_product in order.orderproducts.filter(
                        correction__isnull=True):
                    order_products.append({
                        "id": order_product.id,
                        "name": "%s (%s)" % (
                            order_product.product.name,
                            order_product.product.supplier.name
                        ),
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


class OrderAdminCorrection(GroupRequiredMixin, TemplateView):
    template_name = "ordering/admin/correction.html"
    group_required = ('Uitdeelcoordinatoren', 'Admin')

    def post(self, request, *args, **kwargs):
        user_id = int(request.POST['member_id'])
        order_id = int(request.POST['order_id'])
        order_product_id = int(request.POST['order_product_id'])
        supplied_percentage = int(request.POST['supplied_percentage'])
        notes = str((request.POST['notes']).strip())
        charge_supplier = True if request.POST.get('charge') else False

        order_product = OrderProduct.objects.get(id=order_product_id,
                                                 order_id=order_id,
                                                 order__user_id=user_id)

        OrderProductCorrection.objects.create(
            order_product=order_product,
            supplied_percentage=supplied_percentage,
            notes=notes,
            charge_supplier=charge_supplier
        )

        messages.add_message(request, messages.SUCCESS,
                             "De correctie is succesvol aangemaakt.")

        return redirect(
            reverse('orderadmin_correction', args=args, kwargs=kwargs))

    def supplier_corrections(self):
        order_round = OrderRound.objects.get(pk=self.kwargs.get('pk'))
        """
        corrections[supplier][product]=
                  {  'corrections'    : corrections[],
                     'amount'         : int,
                     'total_supplied' : precentage
                  }
        """
        corr_sppl = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        # get all corrections for suppliers in this order round
        corrections = OrderProductCorrection.objects.filter(
            order_product__order__order_round=order_round).filter(
            charge_supplier=True).order_by(
            "order_product__product__supplier", "order_product__order__user")

        # build corrections per supplier per product
        for correction in corrections:
            product = correction.order_product.product
            supplier = product.supplier
            corr_sppl[supplier][product]['corrections'].append(correction)

        """
        now we have all corrections per supplier per product,
        we can calculate totals
        """
        for s, prd in corr_sppl.items():
            for p, tpp in prd.items():
                # calculate totals per product
                tpp['amount'] = self.calc_amount(tpp['corrections'])
                tpp['perc_supplied'] = self.calc_supplied(tpp['corrections'])
                # and convert defaultdict to normal dict for use in template
                corr_sppl[s][p] = dict(tpp)

        # convert defaultdict to dict for use in template
        for s, op in corr_sppl.items():
            corr_sppl[s] = dict(op)

        return dict(corr_sppl)

    def voko_corrections(self):
        order_round = OrderRound.objects.get(pk=self.kwargs.get('pk'))
        # get all corrections for VOKO in this order round
        return OrderProductCorrection.objects.filter(
            order_product__order__order_round=order_round).filter(
                charge_supplier=False).order_by(
                "order_product__order__user")

    def calc_amount(self, product_corrections):
        """
        helper function to calculate total amount ordered
        """
        total_ordered = 0
        for correction in product_corrections:
            total_ordered += correction.order_product.amount
        return total_ordered

    def calc_supplied(self, supplier_corrections):
        """
        helper function to calculate total percentage suppplied
        """
        total_suppl = 0
        total_ordered = 0
        for corr in supplier_corrections:
            total_ordered += corr.order_product.amount
            total_suppl += corr.order_product.amount * corr.supplied_percentage

        corr_perc = Decimal(total_suppl/total_ordered).quantize(
            Decimal('.01'), rounding=ROUND_DOWN)
        return corr_perc

    def products(self):
        # TODO also return stock products
        order_round = OrderRound.objects.get(pk=self.kwargs.get('pk'))
        return order_round.products.all().order_by('name')

    def order_round(self):
        return OrderRound.objects.get(pk=self.kwargs.get('pk'))


class OrderAccounts(GroupRequiredMixin, DetailView):
    model = OrderRound
    template_name = "ordering/admin/orderround_accounts.html"
    group_required = ('Admin')


class OrderAdminMassCorrection(GroupRequiredMixin, View):
    group_required = ('Uitdeelcoordinatoren', 'Admin')

    def post(self, request, *args, **kwargs):
        order_round = OrderRound.objects.get(pk=self.kwargs.get('pk'))
        product_id = request.POST['product_id']
        product = Product.objects.get(order_round=order_round,
                                      id=product_id)
        product.create_corrections()

        messages.add_message(request, messages.SUCCESS,
                             "De correcties zijn succesvol aangemaakt.")

        return redirect(
            reverse('orderadmin_correction', args=args, kwargs=kwargs))


class ProductAdminMixin(GroupRequiredMixin):
    def _convert_price(self, price):
        if type(price) is str:
            price = price.lstrip('\\u20ac')  # Strip off euro sign
        else:
            price = str(price)
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
        return HttpResponseRedirect(
            reverse('create_draft_products', args=args, kwargs=kwargs))

    def form_valid(self, form):
        try:
            self.create_draft_products_from_spreadsheet(
                self.request.FILES['product_list'])
        except Exception as e:
            messages.add_message(
                self.request, messages.ERROR,
                "Bestand kon niet worden ingelezen. Error: %s" % e)

        return redirect(reverse('create_draft_products', kwargs=self.kwargs))

    def create_draft_products_from_spreadsheet(self, file_handler):
        f = NamedTemporaryFile(delete=False)
        f.write(file_handler.read())
        f.close()

        workbook = openpyxl.load_workbook(f.name, read_only=True)
        sheet = workbook.get_active_sheet()
        PRODUCT_NAME, DESCRIPTION, UNIT, PRICE, MAX, CATEGORY = list(
            range(0, 6))

        for idx, row in enumerate(sheet.rows):
            name, description, unit, price, maximum, category = (
                row[PRODUCT_NAME].value,
                row[DESCRIPTION].value,
                row[UNIT].value,
                row[PRICE].value,
                row[MAX].value,
                row[CATEGORY].value
            )

            if not name or idx == 0:
                continue  # skips header and empty rows

            self._create_draft_product(
                {'name': name,
                 'description': description if description else "",
                 'unit': unit,
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
        for dp in DraftProduct.objects.filter(
                order_round=self.current_order_round,
                supplier=self.supplier).order_by('is_valid', 'id'):
            dp.validate()
            yield dp

    def category_choices(self):
        return [pc.name for pc in ProductCategory.objects.all()]

    def _parse_draft_product_post_data(self):
        """
        yields (product_index, field, data)
        """
        for key in self.request.POST:
            try:
                regex_match = re.match(r"^product_([a-z_]+)_(\d+)$", key)
                if not regex_match:
                    continue

                field, index = regex_match.groups()
                index = int(index)
                data = str(self.request.POST[key])

                sys.stdout.flush()

                if not data:
                    data = None
                elif data.isdigit():
                    data = int(data)

                if index == 0:  # the first (hidden) row
                    continue

                yield index, field, data

            except ValueError:
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
        old_draft_products = DraftProduct.objects.filter(
            order_round=self.current_order_round,
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
        for dp in DraftProduct.objects.filter(
                supplier=self.supplier,
                order_round=self.current_order_round):
            prod = dp.create_product()
            dp.delete()
            prod.determine_if_product_is_new_and_set_label()


class ProductAdminMain(GroupRequiredMixin, ListView):
    group_required = 'Boeren'

    def get_context_data(self, **kwargs):
        ctx = super(ProductAdminMain, self).get_context_data()
        ctx['current_order_round'] = get_current_order_round()
        ctx['last_ten_orders_with_notes'] = Order.objects.filter(
            user_notes__isnull=False).order_by('-id')[:10]
        ctx['last_ten_orders_with_notes'] = Order.objects.filter(
            user_notes__isnull=False).order_by('-id')[:10]
        return ctx

    def get_queryset(self):
        return Supplier.objects.all().order_by("id")

    template_name = "ordering/admin/suppliers.html"


class RedirectToMailingView(GroupRequiredMixin, DetailView):
    group_required = 'Boeren'
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

        user_ids = [user.pk for user in queryset]
        request.session['mailing_user_ids'] = user_ids

        return HttpResponseRedirect(
            reverse("admin_preview_mail", args=(mailing_id,)))


class StockAdminView(GroupRequiredMixin, ListView):
    group_required = ('Boeren', 'Admin')
    template_name = "ordering/admin/stock.html"

    def get_queryset(self):
        return Product.objects.filter(order_round__isnull=True,
                                      enabled=True).order_by("id")

    def get_context_data(self, **kwargs):
        context = super(StockAdminView, self).get_context_data(**kwargs)

        context['product_units'] = ProductUnit.objects.all()
        context['suppliers'] = Supplier.objects.all()
        context['categories'] = ProductCategory.objects.all()

        return context


class ProductStockApiView(GroupRequiredMixin, View):
    group_required = ('Boeren', 'Admin')

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(ProductStockApiView, self).dispatch(request, *args,
                                                         **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            amount = int(request.POST['amount'])
            stock_type = request.POST['type']
            notes = request.POST['notes']
            base_price = Decimal(request.POST['base_price'])

            product_id = request.POST['product_id']
            product = Product.objects.get(id=product_id)

            assert product.enabled
            assert product.order_round is None

        except (IndexError, ValueError, AssertionError,
                Product.DoesNotExist, MultiValueDictKeyError):
            return HttpResponse(status=400)

        if base_price != product.base_price:
            # Clone product but change price
            product.pk = None
            product.base_price = base_price
            product.save()

            # Cannot decrease inventory for new product
            assert stock_type == ProductStock.TYPE_ADDED

            messages.add_message(request, messages.WARNING,
                                 "Product '%s' gekloond met nieuwe prijs."
                                 % product.name)

        ProductStock.objects.create(
            product=product, amount=amount,
            notes=notes, type=stock_type
        )

        messages.add_message(request, messages.SUCCESS,
                             "De voorraad voor product '%s' is bijgewerkt."
                             % product.name)
        return HttpResponse(status=201)


class ProductApiView(GroupRequiredMixin, View):
    group_required = ('Boeren', 'Admin')

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        return super(ProductApiView, self).dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        category_id = request.POST.get('category')
        name = request.POST.get('name')
        description = request.POST.get('description')
        unit_id = request.POST.get('unit')
        base_price = request.POST.get('base_price')
        supplier_id = request.POST.get('supplier')

        stock = request.POST.get('stock')

        assert name
        assert supplier_id, supplier_id

        # For now, create Stock product
        try:
            product = Product.objects.create(
                name=name,
                description=description,
                unit_id=unit_id,
                category_id=category_id,
                base_price=base_price,
                supplier_id=supplier_id
            )
        except IntegrityError:
            return HttpResponse(status=400)

        messages.add_message(request, messages.SUCCESS,
                             "Product '%s' toegevoegd."
                             % product.name)

        if stock:
            ProductStock.objects.create(
                product=product,
                amount=stock
            )

            messages.add_message(request, messages.SUCCESS,
                                 "De voorraad voor product '%s' is bijgewerkt."
                                 % product.name)

        return HttpResponse(status=201)
