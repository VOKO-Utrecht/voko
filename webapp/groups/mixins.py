from braces.views._access import AccessMixin
from django.core.exceptions import PermissionDenied


class IsAdminMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if (not request.user.is_superuser
            and not request.user.groups.filter(
                name__in=['Admin'])):
            raise PermissionDenied

        return super(IsAdminMixin, self).dispatch(
            request, *args, **kwargs)
