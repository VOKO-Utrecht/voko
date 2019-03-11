from braces.views._access import AccessMixin
from django.core.exceptions import PermissionDenied


class UserIsInvolvedMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        ride = self.get_object()
        if (
            request.user != ride.driver and
            request.user != ride.codriver and
            request.user not in ride.coordinators.all() and
            not request.user.groups.filter(name='Transportcoordinatoren').exists()
        ):
            raise PermissionDenied

        return super(UserIsInvolvedMixin, self).dispatch(
            request, *args, **kwargs)
