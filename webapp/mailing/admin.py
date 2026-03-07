from django import forms
from django.contrib import admin
from django.shortcuts import redirect, render
from django.urls import path

from mailing.models import MailTemplate, MailTemplateTag


class ApplyTagsForm(forms.Form):
    tags = forms.ModelMultipleChoiceField(
        queryset=MailTemplateTag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
    )


class MailTemplateAdmin(admin.ModelAdmin):
    list_display = [
        "id", "title", "subject", "from_email", "is_active", "get_tags", "created", "modified"
    ]
    list_filter = ["is_active", "tags"]
    filter_horizontal = ["tags"]
    ordering = ("-id", "modified")
    actions = ["apply_tags_action"]

    def get_tags(self, obj):
        return ", ".join(tag.name for tag in obj.tags.all())
    get_tags.short_description = "Tags"

    def get_urls(self):
        urls = super().get_urls()
        custom = [path("apply-tags/", self.admin_site.admin_view(self.apply_tags_view), name="mailing_apply_tags")]
        return custom + urls

    @admin.action(description="Add tags to selected templates")
    def apply_tags_action(self, request, queryset):
        selected_ids = ",".join(str(obj.pk) for obj in queryset)
        return redirect(f"apply-tags/?selected_ids={selected_ids}")

    def apply_tags_view(self, request):
        selected_ids = request.GET.get("selected_ids", "") or request.POST.get("selected_ids", "")
        ids = [int(i) for i in selected_ids.split(",") if i]
        templates = MailTemplate.objects.filter(pk__in=ids)

        if request.method == "POST":
            form = ApplyTagsForm(request.POST)
            if form.is_valid():
                for template in templates:
                    template.tags.add(*form.cleaned_data["tags"])
                self.message_user(request, f"Tags applied to {len(ids)} template(s).")
                return redirect("..")
        else:
            form = ApplyTagsForm()

        return render(request, "admin/mailing/mailtemplate/apply_tags.html", {
            "form": form,
            "count": len(ids),
            "selected_ids": selected_ids,
            **self.admin_site.each_context(request),
        })


admin.site.register(MailTemplate, MailTemplateAdmin)
admin.site.register(MailTemplateTag)
