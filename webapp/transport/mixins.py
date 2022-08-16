from braces.views._access import AccessMixin
from django.core.exceptions import PermissionDenied


class UserIsInvolvedMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        ride = self.get_object()
        if (
            request.user != ride.driver
            and request.user != ride.codriver
            and request.user != ride.distribution_coordinator
            and request.user != ride.transport_coordinator
            and not request.user.groups.filter(
                name__in=['Transportcoordinatoren', 'Admin']
            ).exists()
        ):
            raise PermissionDenied

        return super(UserIsInvolvedMixin, self).dispatch(
            request, *args, **kwargs)


class IsTransportCoordinatorMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if (not request.user.groups.filter(
                name='Transportcoordinatoren').exists()):
            raise PermissionDenied

        return super(IsTransportCoordinatorMixin, self).dispatch(
            request, *args, **kwargs)
