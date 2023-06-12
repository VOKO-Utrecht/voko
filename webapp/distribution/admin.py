from django.contrib import admin
from distribution.models import Shift
from django.utils.translation import ugettext_lazy as _
import datetime
from accounts.models import VokoUser
from constance import config


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
        if self.value() is None:
            return queryset.filter(
                order_round__collect_datetime__gte=get_recent_date())
        elif self.value() == 'All':
            return queryset.filter()


# get a date two months in the past
def get_recent_date():
    return datetime.datetime.now() - datetime.timedelta(days=60)


def format_order_round(obj):
    return "%s %s" % (obj, obj.collect_datetime.strftime("%Y-%m-%d"))


class ShiftAdmin(admin.ModelAdmin):
    class Media:
        css = {
            'all': ('css/shiftadmin.css',),
        }
    list_display = ["date_long_str", "start_str", "end_str", "members_names"]
    ordering = ("-order_round__collect_datetime", "start")
    list_filter = (RecentListFilter,)

    # Show only members who are in the distribution group
    def formfield_for_manytomany(self, db_field, request, **kwargs):
        if db_field.name == "members":
            kwargs["queryset"] = VokoUser.objects.filter(
                groups__id=config.DISTRIBUTION_GROUP).order_by("first_name", "last_name")
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    # Improve order round name in shift creation form
    def get_form(self, request, obj=None, **kwargs):
        form = super(ShiftAdmin, self).get_form(request, obj, **kwargs)
        order_round_field = form.base_fields['order_round']
        order_round_field.label_from_instance = format_order_round
        return form


admin.site.register(Shift, ShiftAdmin)
