from django.contrib.auth.admin import GroupAdmin as BaseGroupAdmin
from django.contrib.auth.models import Group
from groups.models import GroupExt
from django.contrib import admin


class GroupInline(admin.StackedInline):
    model = GroupExt
    can_delete = False


class GroupAdmin(BaseGroupAdmin):
    inlines = (GroupInline, )


admin.site.unregister(Group)
admin.site.register(Group, GroupAdmin)
