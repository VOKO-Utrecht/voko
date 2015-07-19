from django.contrib import admin
from django.db.models.loading import get_models, get_app
from finance.models import Balance

for model in get_models(get_app('finance')):
    if model in (Balance,):
        continue

    admin.site.register(model)


class PaymentListFilter(admin.SimpleListFilter):
    """
    This filter will always return a subset of the instances in a Model, either filtering by the
    user choice or by a default value.
    """

    # TODO: link payment to balance and use that connection

    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'is payment'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'ispayment'

    default_value = None

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        """
        return (
            ('1', 'True'),
            ('0', 'False'),
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        # Compare the requested value to decide how to filter the queryset.
        if self.value() == '1':
            return queryset.filter(notes__contains="iDeal betaling")
        if self.value() == '0':
            return queryset.exclude(notes__contains="iDeal betaling")


class BalanceAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "type", "amount", "notes", "order", "is_payment"]
    ordering = ("-id", )
    list_filter = ("type", PaymentListFilter)
    search_fields = ['notes']

    def is_payment(self, obj):
        return "iDeal betaling" in obj.notes
    is_payment.boolean = True

admin.site.register(Balance, BalanceAdmin)

