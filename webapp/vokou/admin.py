class DeleteDisabledMixin(object):
    def get_actions(self, request):
        actions = super(DeleteDisabledMixin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        return False
