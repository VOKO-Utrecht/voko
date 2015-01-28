from django.contrib import admin
from django.db.models.loading import get_models, get_app
from finance.models import Balance
from .models import Order, OrderProduct

for model in get_models(get_app('ordering')):
    if model == Order:
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
    list_display = ["id", "order_round", "user", "finalized", "total_price"]
    ordering = ("-id", )
    inlines = [OrderProductInline]
    list_filter = ("finalized", )
    actions = (create_credit_for_order, )

admin.site.register(Order, OrderAdmin)
