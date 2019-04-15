from django.contrib import admin
from mailing.models import MailTemplate


class MailTemplateAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "subject", "from_email", "created", "modified"]
    ordering = ("-id", "modified")


admin.site.register(MailTemplate, MailTemplateAdmin)
