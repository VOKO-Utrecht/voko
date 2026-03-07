from django.contrib import admin
from mailing.models import MailTemplate, MailTemplateTag


class MailTemplateAdmin(admin.ModelAdmin):
    list_display = [
        "id", "title", "subject", "from_email", "is_active", "get_tags", "created", "modified"
    ]
    list_filter = ["is_active", "tags"]
    filter_horizontal = ["tags"]
    ordering = ("-id", "modified")

    def get_tags(self, obj):
        return ", ".join(tag.name for tag in obj.tags.all())
    get_tags.short_description = "Tags"


admin.site.register(MailTemplate, MailTemplateAdmin)
admin.site.register(MailTemplateTag)
