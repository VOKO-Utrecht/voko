from django.contrib import admin
from django.db import OperationalError
from django.db.models.loading import get_models, get_app
import sys
from finance.models import Balance
from .models import Order, OrderProduct, Product, OrderRound, ProductCategory

for model in get_models(get_app('ordering')):
    if model in (Order, Product, OrderRound):
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
    list_display = ["id", "order_round", "user", "paid", "total_price", "user_notes"]
    ordering = ("-id", )
    # inlines = [OrderProductInline]  ## causes timeout
    list_filter = ("paid", )
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
    list_display = ["name", 'description', "order_round", "supplier", "category", "base_price", "maximum_total_order"]
    ordering = ("-id", )
    list_filter = ("order_round", "supplier", "category")
    actions = prod_cat_actions
    list_per_page = 500

admin.site.register(Product, ProductAdmin)


class OrderRoundAdmin(admin.ModelAdmin):
    list_display = ["id", "open_for_orders", "closed_for_orders", "collect_datetime",
                    "markup_percentage", "transaction_costs", "order_placed"]
    ordering = ("-id", )

admin.site.register(OrderRound, OrderRoundAdmin)

