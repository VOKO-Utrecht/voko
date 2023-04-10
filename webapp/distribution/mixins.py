from braces.views._access import AccessMixin
from django.core.exceptions import PermissionDenied


class UserIsInvolvedWithShiftMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        shift = self.get_object()
        if (
            request.user not in shift.members.all()
            and not request.user.groups.filter(
                name='Uitdeelcoordinatoren'
            ).exists()
        ):
            raise PermissionDenied

        return super(UserIsInvolvedWithShiftMixin, self).dispatch(
            request, *args, **kwargs)


class IsDistributionCoordinatorMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if (not request.user.is_superuser
            and not request.user.groups.filter(
                name__in=['Uitdeelcoordinatoren', 'Admin'])):
            raise PermissionDenied

        return super(IsDistributionCoordinatorMixin, self).dispatch(
            request, *args, **kwargs)


class IsInDistributionMixin(AccessMixin):
    def dispatch(self, request, *args, **kwargs):
        if (not request.user.is_superuser
            and not request.user.groups.filter(
                name__in=['Uitdeelcoordinatoren', 'Uitdeel', 'Admin'])):
            raise PermissionDenied

        return super(IsInDistributionMixin, self).dispatch(
            request, *args, **kwargs)
