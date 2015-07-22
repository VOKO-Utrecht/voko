from django.contrib import admin
from django.db.models.loading import get_models, get_app
from finance.models import Balance, Payment

for model in get_models(get_app('finance')):
    if model in (Balance, Payment):
        continue

    admin.site.register(model)


class PaymentListFilter(admin.SimpleListFilter):
    """
    This filter will always return a subset of the instances in a Model, either filtering by the
    user choice or by a default value.
    """

    # TODO: link payment to balance and use that connection

    title = 'is payment'
    parameter_name = 'ispayment'
    default_value = None

    def lookups(self, request, model_admin):
        return (
            ('1', 'True'),
            ('0', 'False'),
        )

    def queryset(self, request, queryset):
        # Compare the requested value to decide how to filter the queryset.
        if self.value() == '1':
            return queryset.filter(notes__contains="iDeal betaling")
        if self.value() == '0':
            return queryset.exclude(notes__contains="iDeal betaling")


class CorrectionListFilter(admin.SimpleListFilter):
    """
    This filter will always return a subset of the instances in a Model, either filtering by the
    user choice or by a default value.
    """

    # TODO: link payment to balance and use that connection

    title = 'is correction'
    parameter_name = 'iscorr'
    default_value = None

    def lookups(self, request, model_admin):
        return (
            ('1', 'True'),
            ('0', 'False'),
        )

    def queryset(self, request, queryset):
        # Compare the requested value to decide how to filter the queryset.
        if self.value() == '1':
            return queryset.filter(correction__isnull=False)
        if self.value() == '0':
            return queryset.filter(correction__isnull=True)


class BalanceAdmin(admin.ModelAdmin):
    list_display = ["id", "created", "modified", "user", "type", "amount", "notes", "order", "is_correction", "is_payment"]
    ordering = ("-id", )
    list_filter = ("type", PaymentListFilter, CorrectionListFilter)
    search_fields = ['notes']

    def is_correction(self, obj):
        return True if obj.correction else False
    is_correction.boolean = True

    def is_payment(self, obj):
        return "iDeal betaling" in obj.notes
    is_payment.boolean = True


class PaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "created", "amount", "order",  "transaction_id", "succeeded"]
    ordering = ("-id", )
    list_filter = ("succeeded",)


admin.site.register(Balance, BalanceAdmin)
admin.site.register(Payment, PaymentAdmin)

