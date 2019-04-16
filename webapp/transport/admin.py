from django.contrib import admin

from transport.models import Route, Ride


class RouteAdmin(admin.ModelAdmin):
    list_display = ["name", "suppliers_names"]
    ordering = ("-id", )


class RideAdmin(admin.ModelAdmin):
    list_display = ["date", "route", "driver", "codriver"]
    ordering = ("order_round__collect_datetime", "route")

    def get_form(self, request, obj=None, **kwargs):
        form = super(RideAdmin, self).get_form(request, obj, **kwargs)
        order_round_field = form.base_fields['order_round']
        order_round_field.label_from_instance = format_order_round
        return form


def format_order_round(obj):
    return "%s %s" % (obj, obj.collect_datetime.strftime("%Y-%m-%d"))


admin.site.register(Route, RouteAdmin)
admin.site.register(Ride, RideAdmin)
