from django.contrib import admin

from docs.models import Document, Link


class DocumentAdmin(admin.ModelAdmin):
    list_display = ["created", "name", "file"]
    ordering = ("-id", )


admin.site.register(Document, DocumentAdmin)

class LinkAdmin(admin.ModelAdmin):
    list_display = ["created", "name", "url"]
    ordering = ("-id", )

admin.site.register(Link, LinkAdmin)
