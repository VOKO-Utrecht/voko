from django.db import models
from django.utils.text import slugify
from django_extensions.db.models import TimeStampedModel
from django.conf import settings
from ordering.models import Supplier

class Route(TimeStampedModel):
    class Meta:
        verbose_name = 'Route'
        verbose_name_plural = 'Routes'

    name = models.CharField(max_length=100)
    suppliers = models.ManyToManyField(Supplier)
    slug = models.SlugField(unique=True, editable=False, max_length=100)

    def save(self, **kwargs):
        self.slug = slugify(self.name)
        return super(Route, self).save(**kwargs)

    def __str__(self):
        return self.name

    @property
    def suppliers_names(self):
        return  list(map(lambda s: s.name, self.suppliers.all()))

class Ride(TimeStampedModel):
    class Meta:
        verbose_name = 'Ride'
        verbose_name_plural = 'Rides'

    date = models.DateField()
    # order_round = models.ForeignKey("OrderRound", related_name="ride")
    route = models.ForeignKey(Route, models.SET_NULL, null=True, related_name="rides");
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="rides_as_driver")
    codriver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="rides_as_codriver")
    slug = models.SlugField(unique=True, editable=False, max_length=100)

    def save(self, **kwargs):
        self.slug = slugify(self.date.isoformat()+'-'+str(self.route))
        return super(Ride, self).save(**kwargs)

    def __str__(self):
        return self.date.isoformat()+'-'+str(self.route)

