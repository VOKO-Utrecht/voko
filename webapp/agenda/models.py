from datetime import datetime

from accounts.models import Address
from django.db import models
from django_extensions.db.models import TimeStampedModel
from tinymce.models import HTMLField


class Event(models.Model):
    class Meta:
        abstract = True
        managed = True

    id = models.AutoField(primary_key=True)
    title = models.CharField(verbose_name="titel", max_length=150)
    short_description = models.CharField(
        verbose_name="korte beschrijving", max_length=300, blank=True, null=True
    )
    long_description = HTMLField(
        verbose_name="lange beschrijving", blank=True, null=True
    )
    date = models.DateField(verbose_name="datum", default=datetime.now)
    time = models.TimeField(verbose_name="tijd", default=datetime.now)
    address = models.ForeignKey(
        Address, null=True, blank=True, on_delete=models.CASCADE
    )

    def __str__(self):
        return "%s - %s" % (self.title, self.date)


class PersistentEvent(Event, TimeStampedModel):
    class Meta:
        verbose_name = "evenement"
        verbose_name_plural = "evenementen"
        abstract = False
        managed = True


class TransientEvent(Event):
    class Meta:
        abstract = False
        managed = False

    is_shift = models.BooleanField(default=False)
    org_model = models.CharField(max_length=50, blank=True, null=True)
    org_id = models.IntegerField(blank=True, null=True)

    def save(*args, **kwargs):
        pass  # avoid exceptions if called
