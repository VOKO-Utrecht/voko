from braces.views._access import AccessMixin
from django.core.exceptions import PermissionDenied


class UserOwnsObjectMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if request.user != self.get_object().user:
            raise PermissionDenied

        return super(UserOwnsObjectMixin, self).dispatch(
            request, *args, **kwargs)
