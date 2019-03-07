from braces.views._access import AccessMixin
from django.core.exceptions import PermissionDenied

class UserIsDrivingMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        ride = self.get_object()
        if request.user != ride.driver and request.user != ride.codriver:
            raise PermissionDenied

        return super(UserIsDrivingMixin, self).dispatch(
            request, *args, **kwargs)
