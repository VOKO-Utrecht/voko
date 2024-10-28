import csv
from django.contrib import admin
from django.db import OperationalError, ProgrammingError
import sys

from django.http import HttpResponse

from finance.models import Balance
from vokou.admin import DeleteDisabledMixin
from .models import (Order, OrderProduct, Product, OrderRound, ProductCategory,
                     OrderProductCorrection, ProductStock, Supplier,
                     ProductUnit, DraftProduct, PickupLocation)


class OrderProductInline(admin.TabularInline):
    model = OrderProduct


def create_credit_for_order(modeladmin, request, queryset):
    for order in queryset:
        Balance.objects.create(user=order.user,
                               type="CR",
                               amount=order.total_price,
                               notes="Bestelling #%d contant betaald"
                                     % order.pk)


create_credit_for_order.short_description = "Contant betaald"


def dutch_decimal(value):
    return str(value).replace('.', ',')


def export_orders_for_financial_admin(modeladmin, request, queryset):
    field_names = [
        'Bestelling ID',
        'Lid',
        'Datum',
        'Ronde',
        'Totaalsom producten (incl. marge)',
        'ledenbijdrage',
        'Transactiekosten',
        'Betaald',
        'Verrekening debit/credit',
        'Totaalbedrag']

    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response[
        'Content-Disposition'] = 'attachment; filename=orders_export.csv'

    writer = csv.writer(response)
    writer.writerow(field_names)

    for order in queryset.filter(paid=True):
        # Why multiple payments? Because of (historical) corner case with
        # double payment.
        payments = order.payments.filter(succeeded=True)
        actually_paid = sum([p.amount for p in payments])

        dd = dutch_decimal
        row = [
            order.id,
            "{0} ({1})".format(order.user, order.user_id),
            order.modified.date(),
            order.order_round_id,
            dd(sum([odp.total_retail_price
                    for odp in order.orderproducts.all()])),
            dd(order.member_fee),
            dd(order.order_round.transaction_costs),
            dd(actually_paid).replace('.', ','),
            dd(order.debit.amount - actually_paid),
            dd(order.debit.amount)
        ]
        writer.writerow(row)

    return response


export_orders_for_financial_admin.short_description = (
    "Exporteer voor financiële admin")


class OrderAdmin(DeleteDisabledMixin, admin.ModelAdmin):
    list_display = ["id", "created", "order_round", "user", "finalized",
                    "paid", "total_price", "user_notes"]
    ordering = ("-id", )
    # inlines = [OrderProductInline]  ## causes timeout
    list_filter = ("paid", "finalized", "order_round")
    actions = (create_credit_for_order, export_orders_for_financial_admin)


# Generate actions for categories
def generate_action(category):
    def fn(modeladmin, request, queryset):
        for product in queryset:
            product.category = category
            product.save()
    return fn


thismodule = sys.modules[__name__]

prod_cat_actions = []
try:
    for category in ProductCategory.objects.all():
        setattr(thismodule, "fn_%s" % category.id, generate_action(category))
        fn = getattr(thismodule, "fn_%s" % category.id)
        fn.short_description = "Set category to '%s'" % category.name
        fn.__name__ = str(category.id)
        prod_cat_actions.append(fn)

    def remove_category(_, __, queryset):
        for product in queryset:
            product.category = None
            product.save()
    remove_category.short_description = "Remove category from product"
    prod_cat_actions.append(remove_category)

except (OperationalError, ProgrammingError):
    pass  # This is to prevent failure during an initial migration run


class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", 'description', "order_round", "supplier",
                    "category", "base_price", "maximum_total_order",
                    "new"]
    ordering = ("-id", )
    list_filter = ("order_round", "supplier", "category", "new")
    actions = prod_cat_actions
    list_per_page = 500


class ProductStockAdmin(DeleteDisabledMixin, admin.ModelAdmin):
    list_display = ["id", "created", "product", 'amount', "type", "notes"]
    ordering = ("-id", "created", "product", "amount", "type", "notes")
    list_filter = ("type",)
    raw_id_fields = ('product',)


class OrderRoundAdmin(DeleteDisabledMixin, admin.ModelAdmin):
    list_display = ["id", "open_for_orders", "closed_for_orders",
                    "collect_datetime", "pickup_location", "markup_percentage",
                    "transaction_costs", "reminder_hours_before_closing",
                    "order_placed", "reminder_sent"]
    ordering = ("-id", )


class OrderProductCorrectionAdmin(DeleteDisabledMixin, admin.ModelAdmin):
    list_display = ["id", 'created', 'order_product', "supplied_percentage",
                    "notes", "credit", "charge_supplier"]
    ordering = ("-id", 'charge_supplier', 'supplied_percentage', 'created')
    list_filter = ("charge_supplier",)
    raw_id_fields = ('order_product',)


class OrderProductAdmin(DeleteDisabledMixin, admin.ModelAdmin):
    list_display = ["id", 'order', 'order_paid', "product", "amount",
                    "stock_product", "base_price", "retail_price"]
    ordering = ("-id", 'order', 'product')
    list_filter = ("order__paid", "product__order_round")
    raw_id_fields = ('order', 'product')

    def order_paid(self, obj):
        return obj.order.paid is True
    order_paid.boolean = True

    def stock_product(self, obj):
        return obj.product.is_stock_product()
    stock_product.boolean = True


class SupplierAdmin(DeleteDisabledMixin, admin.ModelAdmin):
    list_display = ["name", "is_active"]
    ordering = ("name",)
    list_filter = ("is_active",)


class CategoryAdmin(DeleteDisabledMixin, admin.ModelAdmin):
    pass


class ProductUnitAdmin(DeleteDisabledMixin, admin.ModelAdmin):
    pass


class DraftProductAdmin(admin.ModelAdmin):
    pass


class PickupLocationAdmin(admin.ModelAdmin):
    list_display = ["name", "is_default"]


admin.site.register(Order, OrderAdmin)
admin.site.register(OrderProduct, OrderProductAdmin)
admin.site.register(OrderProductCorrection, OrderProductCorrectionAdmin)
admin.site.register(OrderRound, OrderRoundAdmin)
admin.site.register(DraftProduct, DraftProductAdmin)
admin.site.register(ProductUnit, ProductUnitAdmin)
admin.site.register(ProductCategory, CategoryAdmin)
admin.site.register(ProductStock, ProductStockAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(PickupLocation, PickupLocationAdmin)
