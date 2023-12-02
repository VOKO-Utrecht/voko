from django.contrib import admin
from tinymce.models import HTMLField
from tinymce.widgets import AdminTinyMCE
from news.models import Newsitem

class NewsitemAdmin(admin.ModelAdmin):
    list_display = ["title","publish","created"]
    formfield_overrides = {
        HTMLField: {'widget': AdminTinyMCE(attrs={'cols': 10, 'rows': 50})}
    }


admin.site.register(Newsitem, NewsitemAdmin)
