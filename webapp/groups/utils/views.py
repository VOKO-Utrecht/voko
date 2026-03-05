from accounts.models import VokoUser
from django.contrib.auth.models import Group
from groups.utils.forms import GroupManagerForm
from django.views.generic import FormView
from django.core.exceptions import ImproperlyConfigured


class GroupmanagerFormView(FormView):
    template_name = None
    group_pk = None
    success_url = None
    form_class = GroupManagerForm
    model = Group

    def get_group_pk(self):
        """Override this method to return the group pk dynamically."""
        if self.group_pk is None:
            raise ImproperlyConfigured(
                "GroupmanagerFormView requires group primary key. Set group_pk or override get_group_pk()."
            )
        return self.group_pk

    def get_form_kwargs(self):
        """Passes the request object to the form class.
        This is necessary to pass group pk to the form"""

        kwargs = super(GroupmanagerFormView, self).get_form_kwargs()
        kwargs["group_pk"] = self.get_group_pk()
        return kwargs

    def post(self, request, *args, **kwargs):
        group_pk = self.get_group_pk()
        transport_group = Group.objects.get(pk=group_pk)
        form = GroupManagerForm(request.POST, group_pk=group_pk)
        if form.is_valid():
            if "cancel" in request.POST:
                return self.success_url
            else:
                user_ids = request.POST.getlist("users", [])
                self._update_groupmembers(transport_group, user_ids)
        return super().form_valid(form)

    def _update_groupmembers(self, group, members_ids):
        members = VokoUser.objects.all().filter(pk__in=members_ids)
        for m in members:
            if group.user_set.all().filter(id=m.id).first() is None:
                m.groups.add(group)

        members_ids = [int(item) for item in members_ids]
        for m in group.user_set.all():
            if m.id not in members_ids:
                m.groups.remove(group)
