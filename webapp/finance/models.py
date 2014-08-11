from django.db import models
from vokou import settings


class Payment(models.Model):
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    # Might be reduntant / non-normalized?
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="user")

    # TODO: add more fields

    # TODO: succeeded payment creates credit.

    def is_paid(self):  # Placeholder
        return True

    def __unicode__(self):
        return "Payment of E%s" % self.amount


class BalanceManager(models.Manager):
    use_for_related_fields = True

    def credit(self):
        credit_objs = super(BalanceManager, self).get_queryset().filter(type="CR")
        debit_objs = super(BalanceManager, self).get_queryset().filter(type="DR")
        credit_sum = sum([b.amount for b in credit_objs])
        debit_sum = sum([b.amount for b in debit_objs])

        return credit_sum - debit_sum

    def debit(self):
        return -self.credit()


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
