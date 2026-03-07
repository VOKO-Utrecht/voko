from django.contrib import admin
from mailing.models import MailTemplate


class MailTemplateAdmin(admin.ModelAdmin):
    list_display = [
        "id", "title", "subject", "from_email", "is_active", "created", "modified"
    ]
    list_filter = ["is_active"]
    ordering = ("-id", "modified")


admin.site.register(MailTemplate, MailTemplateAdmin)
