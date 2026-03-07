from django.contrib import admin
from tinymce.models import HTMLField
from tinymce.widgets import AdminTinyMCE

from pages.models import Page


class PageAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "published", "modified"]
    prepopulated_fields = {"slug": ("title",)}
    formfield_overrides = {
        HTMLField: {"widget": AdminTinyMCE(attrs={"cols": 10, "rows": 50})}
    }


admin.site.register(Page, PageAdmin)
