from django.contrib import admin
from finance.models import Balance, Payment
from vokou.admin import DeleteDisabledMixin


class BalanceFilterMixin(object):
    default_value = None

    def lookups(self, request, model_admin):
        return (('1', 'True'),
                ('0', 'False'))


class PaymentListFilter(BalanceFilterMixin, admin.SimpleListFilter):
    """
    Filter Balances by being payment credit or not
    """
    title = 'is payment'
    parameter_name = 'ispayment'

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.exclude(payment=None)
        if self.value() == '0':
            return queryset.filter(payment=None)


class CorrectionListFilter(BalanceFilterMixin, admin.SimpleListFilter):
    """
    Filter Balances on being the result of corrections or not
    """
    title = 'is correction'
    parameter_name = 'iscorr'

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(correction__isnull=False)
        if self.value() == '0':
            return queryset.filter(correction__isnull=True)


class DebetListFilter(BalanceFilterMixin, admin.SimpleListFilter):
    """
    Filter Balances on being the result of corrections or not
    """
    title = 'is debet'
    parameter_name = 'isdebet'

    def queryset(self, request, queryset):
        if self.value() == '1':
            return queryset.filter(order__isnull=False)
        if self.value() == '0':
            return queryset.filter(order__isnull=True)


class BalanceAdmin(DeleteDisabledMixin, admin.ModelAdmin):
    list_display = ["id", "created", "modified", "user", "type", "amount", "notes", "is_correction", "is_payment", 'is_order_debit']
    ordering = ("-id", )
    list_filter = ("type", PaymentListFilter, CorrectionListFilter, DebetListFilter)
    search_fields = ['notes']

    def is_correction(self, obj):
        return obj.correction is not None
    is_correction.boolean = True

    def is_payment(self, obj):
        return obj.payment is not None
    is_payment.boolean = True

    def is_order_debit(self, obj):
        return obj.order is not None
    is_order_debit.boolean = True


class PaymentAdmin(DeleteDisabledMixin, admin.ModelAdmin):
    list_display = ["id", "created", "amount", "order",  "qantani_transaction_id", "succeeded"]
    ordering = ("-id", )
    list_filter = ("succeeded",)


admin.site.register(Balance, BalanceAdmin)
admin.site.register(Payment, PaymentAdmin)

