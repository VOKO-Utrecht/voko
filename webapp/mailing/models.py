from django.db import models
from django_extensions.db.models import TimeStampedModel
from tinymce.models import HTMLField


class MailTemplate(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=100)
    subject = models.CharField(max_length=100, default="VOKO Amersfoort - ")
    from_email = models.CharField(max_length=100, default="", blank=True)
    html_body = HTMLField()

    def __str__(self):
        return "%s (%s)" % (self.title, self.subject)
