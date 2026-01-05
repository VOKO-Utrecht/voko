from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django_extensions.db.models import TimeStampedModel
from ordering.models import Supplier, OrderRound
from agenda.models import TransientEvent
from accounts.models import ReadOnlyVokoUser


class Route(TimeStampedModel):
    class Meta:
        verbose_name = "Route"
        verbose_name_plural = "Routes"

    id = models.AutoField(primary_key=True)
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
        verbose_name = "Ride"
        verbose_name_plural = "Rides"
        # Ensure we don't create multiple rides (and thus identical slugs)
        # for the same order_round (which determines date_str) and route.
        unique_together = ["order_round", "route"]

    id = models.AutoField(primary_key=True)
    order_round = models.ForeignKey(
        OrderRound, on_delete=models.SET_NULL, null=True, related_name="rides"
    )
    route = models.ForeignKey(
        Route, on_delete=models.SET_NULL, null=True, related_name="rides"
    )

    # ReadOnlyVokoUser so selection box in admin works with autocomplete
    driver = models.ForeignKey(
        ReadOnlyVokoUser,
        on_delete=models.CASCADE,
        related_name="rides_as_driver",
    )
    codriver = models.ForeignKey(
        ReadOnlyVokoUser,
        on_delete=models.CASCADE,
        related_name="rides_as_codriver",
    )
    slug = models.SlugField(unique=True, editable=False, max_length=100)

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
    def transport_coordinator(self):
        return self.order_round.transport_coordinator

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
        self.slug = slugify("{}-{}".format(self.date_str, self.route))
        return super(Ride, self).save(**kwargs)

    def as_event(self):
        event = TransientEvent()
        event.address = self.order_round.pickup_location.address
        event.title = f"Transportdienst {self.order_round.pickup_location}"
        event.short_description = (f"<a href=\"{reverse('ride', args={self.slug})}\">"
                                   f"Transportdienst</a> voor ronde {self.order_round.id}")
        event.date = self.date.date()
        event.time = self.date.time()
        event.is_shift = True
        return event

    def __str__(self):
        return "{}-{}".format(self.date_str, self.route)
