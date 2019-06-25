from django.contrib import admin
from distribution.models import Shift


class ShiftAdmin(admin.ModelAdmin):
    list_display = ["date_long_str", "start_str", "end_str", "members_names"]
    ordering = ("order_round__collect_datetime", "start")

    # Improve order round name in shift creation form
    def get_form(self, request, obj=None, **kwargs):
        form = super(ShiftAdmin, self).get_form(request, obj, **kwargs)
        order_round_field = form.base_fields['order_round']
        order_round_field.label_from_instance = format_order_round
        return form


def format_order_round(obj):
    return "%s %s" % (obj, obj.collect_datetime.strftime("%Y-%m-%d"))


admin.site.register(Shift, ShiftAdmin)
