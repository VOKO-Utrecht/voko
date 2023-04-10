from django import forms
from accounts.models import VokoUser


class GroupManagerForm(forms.Form):

    group_pk = None
    users = forms.ModelMultipleChoiceField(
        queryset=VokoUser.objects.all().filter(is_active=True).order_by("first_name", "last_name"), required=False
        )

    def __init__(self, *args, **kwargs):
        self.group_pk = kwargs.pop('group_pk')
        super(GroupManagerForm, self).__init__(*args, **kwargs)
        self.fields['users'].initial = VokoUser.objects.filter(groups__id=self.group_pk)
