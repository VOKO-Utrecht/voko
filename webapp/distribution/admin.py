from django.contrib import admin
from distribution.models import Shift


class ShiftAdmin(admin.ModelAdmin):
    list_display = ["date_long_str", "start_str", "end_str", "members_names"]
    ordering = ("order_round__collect_datetime", "start")


admin.site.register(Shift, ShiftAdmin)
