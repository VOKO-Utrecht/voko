from django.db import models
from django_extensions.db.models import TimeStampedModel
from accounts.models import VokoUser


class EventLog(TimeStampedModel):
    operator = models.ForeignKey(VokoUser, related_name="operator_logs")
    user = models.ForeignKey(VokoUser, null=True, blank=True, related_name="user_logs")
    event = models.TextField()