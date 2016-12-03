from django.apps import apps
from django.contrib import admin
from django.db import OperationalError
import sys
from finance.models import Balance
from .models import Order, OrderProduct, Product, OrderRound, ProductCategory, \
    OrderProductCorrection, ProductStock

for model in apps.get_app_config('ordering').get_models():
    if model in (Order, Product, OrderRound, OrderProductCorrection,
                 ProductStock, OrderProduct):
        continue
    admin.site.register(model)


class OrderProductInline(admin.TabularInline):
    model = OrderProduct


def create_credit_for_order(modeladmin, request, queryset):
    for order in queryset:
        Balance.objects.create(user=order.user,
                               type="CR",
                               amount=order.total_price,
                               notes="Bestelling #%d contant betaald" % order.pk)
create_credit_for_order.short_description = "Contant betaald"


class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "created", "order_round", "user", "finalized", "paid", "total_price", "user_notes"]
    ordering = ("-id", )
    # inlines = [OrderProductInline]  ## causes timeout
    list_filter = ("paid", "finalized", "order_round")
    actions = (create_credit_for_order, )

admin.site.register(Order, OrderAdmin)


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

except OperationalError:
    pass  # This is to prevent failure during an initial migration run


class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", 'description', "order_round", "supplier", "category", "base_price", "maximum_total_order",
                    "new"]
    ordering = ("-id", )
    list_filter = ("order_round", "supplier", "category", "new")
    actions = prod_cat_actions
    list_per_page = 500

admin.site.register(Product, ProductAdmin)


class ProductStockAdmin(admin.ModelAdmin):
    list_display = ["id", "created", "product", 'amount', "type", "notes"]
    ordering = ("-id", "created", "product", "amount", "type", "notes")
    list_filter = ("type",)
    raw_id_fields = ('product',)

admin.site.register(ProductStock, ProductStockAdmin)


class OrderRoundAdmin(admin.ModelAdmin):
    list_display = ["id", "open_for_orders", "closed_for_orders", "collect_datetime",
                    "markup_percentage", "transaction_costs", "order_placed"]
    ordering = ("-id", )

admin.site.register(OrderRound, OrderRoundAdmin)


class OrderProductCorrectionAdmin(admin.ModelAdmin):
    list_display = ["id", 'order_product', "supplied_percentage", "notes", "credit", "charge_supplier"]
    ordering = ("-id", 'charge_supplier', 'supplied_percentage')
    list_filter = ("charge_supplier",)
    raw_id_fields = ('order_product',)

admin.site.register(OrderProductCorrection, OrderProductCorrectionAdmin)


class OrderProductAdmin(admin.ModelAdmin):
    list_display = ["id", 'order', 'order_paid', "product", "amount", "stock_product", "base_price", "retail_price"]
    ordering = ("-id", 'order', 'product')
    list_filter = ("order__paid", "product__order_round")
    raw_id_fields = ('order', 'product')

    def order_paid(self, obj):
        return obj.order.paid is True
    order_paid.boolean = True

    def stock_product(self, obj):
        return obj.product.is_stock_product()
    stock_product.boolean = True

admin.site.register(OrderProduct, OrderProductAdmin)

