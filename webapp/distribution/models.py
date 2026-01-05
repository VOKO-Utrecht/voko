from django.db import models
from django.core.exceptions import ValidationError
from django.utils.text import slugify
from django_extensions.db.models import TimeStampedModel
from django.conf import settings
from ordering.models import OrderRound
from agenda.models import TransientEvent
from django.urls import reverse


class Shift(TimeStampedModel):
    class Meta:
        verbose_name = "Shift"
        verbose_name_plural = "Shifts"
        ordering = ["start"]
        unique_together = ["start", "end", "order_round"]

    id = models.AutoField(primary_key=True)
    order_round = models.ForeignKey(
        OrderRound,
        on_delete=models.SET_NULL,
        null=True,
        related_name="distribution_shifts",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="distribution_shifts"
    )
    start = models.TimeField(help_text="When this shift starts (hh:mm)")
    end = models.TimeField(help_text="When this shift ends (hh:mm)")
    slug = models.SlugField(unique=True, editable=False, max_length=100)

    @property
    def date(self):
        return self.order_round.collect_datetime

    @property
    def date_str(self):
        return self.date.strftime("%Y-%m-%d")

    @property
    def date_long_str(self):
        return self.date.strftime("%d %b %Y")

    @property
    def start_str(self):
        return self.start.strftime("%H:%M")

    @property
    def end_str(self):
        return self.end.strftime("%H:%M")

    @property
    def distribution_coordinator(self):
        return self.order_round.distribution_coordinator

    @property
    def transport_coordinator(self):
        return self.order_round.transport_coordinator

    @property
    def members_names(self):
        return list(map(lambda s: s.get_full_name(), self.members.all()))

    @property
    def key_collectors(self):
        next_order_round = self.order_round.get_next_order_round()
        if next_order_round is None:
            return None
        key_collectors = []
        for ride in next_order_round.rides.all():
            key_collectors.append({"route": ride.route, "codriver": ride.codriver})
        return key_collectors

    def clean(self):
        # If start or end is not set, defer to field-level validation
        if self.start is None or self.end is None:
            return
        if self.start >= self.end:
            raise ValidationError(
                f"De starttijd ({self.start}) van de shift ligt na de eindtijd ({self.end})"
            )

    def save(self, **kwargs):
        self.slug = slugify(self)
        return super(Shift, self).save(**kwargs)

    def as_event(self):
        event = TransientEvent()
        event.address = self.order_round.pickup_location.address
        event.title = f"Uitdeeldienst {self.order_round.pickup_location}"
        event.short_description = (
            f"<a href=\"{reverse('shift', args={self.slug})}\">"
            f"Uitdeeldienst</a> voor ronde {self.order_round.id}"
        )
        event.date = self.date.date()
        event.time = self.start
        event.is_shift = True
        return event

    def __str__(self):
        return "{}-{}-{}".format(self.date_str, self.start_str, self.end_str)
