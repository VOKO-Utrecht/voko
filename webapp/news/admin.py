from django.contrib import admin
from tinymce.models import HTMLField
from tinymce.widgets import AdminTinyMCE
from news.models import Newsitem


def publish_selected_items(modeladmin, request, queryset):
    for item in queryset:
        if not item.publish:
            item.publish = True
            item.save()


publish_selected_items.short_description = "Geselecteerd berichten publiceren"


def unpublish_selected_items(modeladmin, request, queryset):
    for item in queryset:
        if item.publish:
            item.publish = False
            item.save()


unpublish_selected_items.short_description = "Geselecteerd berichten niet (meer) publiceren"


class NewsitemAdmin(admin.ModelAdmin):
    list_display = ["title", "publish", "publish_date", "created"]
    formfield_overrides = {
        HTMLField: {'widget': AdminTinyMCE(attrs={'cols': 10, 'rows': 50})}
    }
    exclude = ['publish_date']
    actions = [publish_selected_items, unpublish_selected_items]


admin.site.register(Newsitem, NewsitemAdmin)
