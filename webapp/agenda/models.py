from django.db import models
from django_extensions.db.models import TimeStampedModel
from datetime import datetime
from accounts.models import Address
from tinymce.models import HTMLField


class Event(TimeStampedModel):

    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=150)
    short_description = HTMLField(blank=True, null=True)
    long_description = HTMLField(blank=True, null=True)
    date_time = models.DateTimeField(default=datetime.now)
    address = models.ForeignKey(Address,
                                null=True,
                                blank=True,
                                on_delete=models.CASCADE)

    def __str__(self):
        return "%s - %s" % (self.title, self.date_time)


class PersistentEvent(Event, TimeStampedModel):
    class Meta:
        verbose_name = "evenement"
        verbose_name_plural = "evenementen"
        abstract = False
        managed = True


class TransientEvent(Event):
    class Meta:
        abstract = True
        managed = False

    is_shift = models.BooleanField(default=False)
    original_model = models.CharField(blank=True, null=True)
    original_id = models.IntegerField(blank=True, null=True)

    def save(*args, **kwargs):
        pass  # avoid exceptions if called
