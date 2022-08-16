from django import forms
from accounts.models import VokoUser
from constance import config


class GroupManagerForm(forms.Form):

    users = forms.ModelMultipleChoiceField(
        queryset=VokoUser.objects.all().order_by("first_name"), required=False
        )

    def __init__(self, *args, **kwargs):
        super(GroupManagerForm, self).__init__(*args, **kwargs)
        self.fields['users'].initial = VokoUser.objects.filter(groups__id=config.TRANSPORT_GROUP)
