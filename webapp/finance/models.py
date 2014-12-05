from django.db import models
from django.conf import settings


class Payment(models.Model):
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    # Might be reduntant / non-normalized?
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="user")

    transaction_id = models.IntegerField()
    transaction_code = models.CharField(max_length=255)
    succeeded = models.BooleanField(default=False)

    # TODO: add more fields
    # TODO: succeeded payment creates credit.

    def _create_credit(self):
        Balance.objects.create(user=self.user,
                               type="CR",
                               amount=self.amount,
                               notes="Credit from Payment #%d" % self.pk)

    def save(self, *args, **kwargs):
        super(Payment, self).save(*args, **kwargs)
        self._create_credit()

    def __unicode__(self):
        return "Payment of E%s" % self.amount


class BalanceManager(models.Manager):
    use_for_related_fields = True

    def _credit(self):
        credit_objs = self.get_queryset().filter(type="CR")
        debit_objs = self.get_queryset().filter(type="DR")
        credit_sum = sum([b.amount for b in credit_objs])
        debit_sum = sum([b.amount for b in debit_objs])

        return credit_sum - debit_sum

    def _debit(self):
        return -self._credit()

    def credit(self):
        _credit = self._credit()
        return _credit if _credit > 0 else 0

    def debit(self):
        _debit = self._debit()
        return _debit if _debit > 0 else 0


class Balance(models.Model):
    # TODO: add sanity check; amount may never be negative.
    TYPES = (
        ("CR", "Credit"),
        ("DR", "Debit"),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="balance")
    type = models.CharField(max_length=2, choices=TYPES)
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    notes = models.TextField()

    def __unicode__(self):
        return "[%s] %s: %s" % (self.user, self.type, self.amount)

    objects = BalanceManager()
