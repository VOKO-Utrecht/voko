from django.contrib import admin

from transport.models import Route, Ride
from django.utils.translation import ugettext_lazy as _
import datetime

# Creates filter for every shift since two months ago
class RecentListFilter(admin.SimpleListFilter):
    title = _('Datum')
    parameter_name = 'date'

    def lookups(self, request, model_admin):
        return (
            (None, _('Recent')),
            ('All', _('All'))
        )

    def choices(self, cl):
        for lookup, title in self.lookup_choices:
            yield {
                'selected': self.value() == lookup,
                'query_string': cl.get_query_string({
                    self.parameter_name: lookup,
                }, []),
                'display': title,
            }

    def queryset(self, request, queryset):
        if self.value() == None:
            return queryset.filter(
                order_round__collect_datetime__gte=get_recent_date())
        elif self.value() == 'All':
            return queryset.filter()

# get a date two months in the past
def get_recent_date():
    return datetime.datetime.now() - datetime.timedelta(days=60)

class RouteAdmin(admin.ModelAdmin):
    list_display = ["name", "suppliers_names"]
    ordering = ("-id", )

class RideAdmin(admin.ModelAdmin):
    list_display = ["date", "route", "driver", "codriver"]
    ordering = ("-order_round__collect_datetime", "route")
    list_filter = (RecentListFilter,)
    
    def get_form(self, request, obj=None, **kwargs):
        form = super(RideAdmin, self).get_form(request, obj, **kwargs)
        order_round_field = form.base_fields['order_round']
        order_round_field.label_from_instance = format_order_round
        return form


def format_order_round(obj):
    return "%s %s" % (obj, obj.collect_datetime.strftime("%Y-%m-%d"))


admin.site.register(Route, RouteAdmin)
admin.site.register(Ride, RideAdmin)
