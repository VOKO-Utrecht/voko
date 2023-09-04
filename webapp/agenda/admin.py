from django.contrib import admin
from agenda.models import PersistentEvent
from tinymce.models import HTMLField
from tinymce.widgets import AdminTinyMCE


class EventAdmin(admin.ModelAdmin):
    list_display = ["title", "date_time"]
    formfield_overrides = {
        HTMLField: {'widget': AdminTinyMCE(attrs={'cols': 10, 'rows': 50})}
        }


admin.site.register(PersistentEvent, EventAdmin)
