from django.db import models
from django.utils.text import slugify
from django_extensions.db.models import TimeStampedModel
from django.conf import settings
from ordering.models import Supplier, OrderRound


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
        return list(map(lambda s: s.name, self.suppliers.all()))


class Ride(TimeStampedModel):
    class Meta:
        verbose_name = 'Ride'
        verbose_name_plural = 'Rides'

    order_round = models.ForeignKey(
        OrderRound, models.SET_NULL, null=True, related_name="rides")
    route = models.ForeignKey(
        Route, models.SET_NULL, null=True, related_name="rides")
    driver = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="rides_as_driver")
    codriver = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="rides_as_codriver")
    coordinators = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="coordinating")
    slug = models.SlugField(
        unique=True, editable=False, max_length=100)

    @property
    def date(self):
        return self.order_round.collect_datetime

    @property
    def date_str(self):
        return self.date.strftime("%Y-%m-%d")

    @property
    def suppliers(self):
        return self.order_round.suppliers

    @property
    def distribution_coordinator(self):
        return self.order_round.distribution_coordinator

    @property
    def orders_per_supplier(self):
        orders_per_supplier = self.order_round.orders_per_supplier
        suppliers_in_route = self.route.suppliers.all()

        return {
            key: orders_per_supplier[key]
            for key in suppliers_in_route
            if key in orders_per_supplier
        }

    def save(self, **kwargs):
        self.slug = slugify('{}-{}'.format(self.date_str, self.route))
        return super(Ride, self).save(**kwargs)

    def __str__(self):
        return '{}-{}'.format(self.date_str, self.route)
