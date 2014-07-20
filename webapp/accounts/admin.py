from django.contrib import admin
from django.db.models.loading import get_models, get_app
from accounts.forms import VokoUserAdmin
from accounts.models import VokoUser

for model in get_models(get_app('accounts')):
    if model == VokoUser:
        continue
    admin.site.register(model)

# Register the new TwoScoopsUserAdmin
admin.site.register(VokoUser, VokoUserAdmin)