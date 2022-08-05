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
