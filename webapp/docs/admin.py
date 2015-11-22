from django.contrib import admin

from docs.models import Document


class DocumentAdmin(admin.ModelAdmin):
    list_display = ["created", "name", "file"]
    ordering = ("-id", )


admin.site.register(Document, DocumentAdmin)