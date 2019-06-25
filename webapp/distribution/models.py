from django.db import models
from django.utils.text import slugify
from django_extensions.db.models import TimeStampedModel
from django.conf import settings
from ordering.models import OrderRound


class Shift(TimeStampedModel):
    class Meta:
        verbose_name = 'Shift'
        verbose_name_plural = 'Shifts'
        ordering = ['start']

    order_round = models.ForeignKey(
        OrderRound,
        models.SET_NULL,
        null=True,
        related_name="distribution_shifts")
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="distribution_shifts")
    start = models.TimeField(
        help_text="When this shift starts")
    end = models.TimeField(
        help_text="When this shifts ends")
    slug = models.SlugField(
        unique=True, editable=False, max_length=100)

    @property
    def date(self):
        return self.order_round.collect_datetime

    @property
    def date_str(self):
        return self.date.strftime("%Y-%m-%d")

    @property
    def date_long_str(self):
        return self.date.strftime("%-d %b %Y")

    @property
    def start_str(self):
        return self.start.strftime("%-H:%M")

    @property
    def end_str(self):
        return self.end.strftime("%-H:%M")

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
        if next_order_round == None:
            return None
        key_collectors = []
        for ride in next_order_round.rides.all():
            key_collectors.append({
                'route': ride.route,
                'codriver': ride.codriver
            })
        return key_collectors

    def save(self, **kwargs):
        self.slug = slugify(self)
        return super(Shift, self).save(**kwargs)

    def __str__(self):
        return '{}-{}-{}'.format(self.date_str, self.start_str, self.end_str)
