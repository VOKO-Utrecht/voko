from django.contrib import admin
from django.db.models.loading import get_models, get_app
from finance.models import Balance

for model in get_models(get_app('finance')):
    if model in (Balance,):
        continue

    admin.site.register(model)


class BalanceAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "type", "amount", "notes", "order"]
    ordering = ("-id", )
    list_filter = ("type", )
    search_fields = ['notes']

admin.site.register(Balance, BalanceAdmin)


