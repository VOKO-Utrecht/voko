from django.db import models
from django.utils.text import slugify
from django_extensions.db.models import TimeStampedModel
from tinymce.models import HTMLField


class Page(TimeStampedModel):
    class Meta:
        verbose_name = "Pagina"
        verbose_name_plural = "Pagina's"

    id = models.AutoField(primary_key=True)
    title = models.CharField(verbose_name="titel", max_length=200)
    slug = models.SlugField(verbose_name="slug", unique=True, max_length=200)
    content = HTMLField(verbose_name="inhoud", blank=True)
    published = models.BooleanField(verbose_name="gepubliceerd", default=False)

    def save(self, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(**kwargs)

    def __str__(self):
        return self.title
