from django.db import models
from django_extensions.db.models import TimeStampedModel
from tinymce.models import HTMLField


class Newsitem(TimeStampedModel):
    class Meta:
        abstract = False
        managed = True
        verbose_name = "nieuwsbericht"
        verbose_name_plural = "nieuwsberichten"

    id = models.AutoField(primary_key=True)
    title = models.CharField(verbose_name="titel", max_length=150)
    publish = models.BooleanField(verbose_name="publiceer", default=False)
    publish_date = models.DateField(verbose_name="publicatiedatum", null=True, blank=True)
    summary = models.CharField(
        verbose_name="samenvatting", max_length=300, blank=True, null=True
    )
    content = HTMLField(
        verbose_name="bericht", blank=True, null=True
    )

    def __str__(self):
        return "%s - %s" % (self.title)
