from django.contrib import admin

from transport.models import Route, Ride


class RouteAdmin(admin.ModelAdmin):
    list_display = ["name", "suppliers_names"]
    ordering = ("-id", )


class RideAdmin(admin.ModelAdmin):
    list_display = ["date", "route", "driver", "codriver"]
    ordering = ("-id", )


admin.site.register(Route, RouteAdmin)
admin.site.register(Ride, RideAdmin)
