from django.contrib import admin

from docs.models import Document, Link


class DocumentAdmin(admin.ModelAdmin):
    list_display = ["created", "name", "file"]
    ordering = ("-id", )


class LinkAdmin(admin.ModelAdmin):
    list_display = ["created", "name", "url"]
    ordering = ("-id", )


admin.site.register(Document, DocumentAdmin)
admin.site.register(Link, LinkAdmin)
