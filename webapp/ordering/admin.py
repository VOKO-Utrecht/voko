from django.contrib import admin
from django.db.models.loading import get_models, get_app
from finance.models import Balance
from .models import Order, OrderProduct, Product, OrderRound

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
    list_display = ["id", "order_round", "user", "finalized", "total_price", "user_notes"]
    ordering = ("-id", )
    inlines = [OrderProductInline]
    list_filter = ("finalized", )
    actions = (create_credit_for_order, )

admin.site.register(Order, OrderAdmin)


class ProductAdmin(admin.ModelAdmin):
    list_display = ["order_round", "supplier", "name", "base_price", "maximum_total_order"]
    ordering = ("-id", )
    list_filter = ("order_round", "supplier")

admin.site.register(Product, ProductAdmin)


class OrderRoundAdmin(admin.ModelAdmin):
    list_display = ["id", "open_for_orders", "closed_for_orders", "collect_datetime",
                    "markup_percentage", "transaction_costs", "order_placed", "suppliers_reminder_sent"]
    ordering = ("-id", )

admin.site.register(OrderRound, OrderRoundAdmin)

