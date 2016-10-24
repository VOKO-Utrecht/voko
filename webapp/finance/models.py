from django.db import models
from django.conf import settings
from django_extensions.db.models import TimeStampedModel


class Payment(TimeStampedModel):
    """
    Represents a payment initiated by our payment service provider.
    """
    amount = models.DecimalField(max_digits=6, decimal_places=2)

    # A Payment is always used to finish an order
    order = models.ForeignKey("ordering.Order", related_name="payments")

    # Credit Balance, for successful payment
    balance = models.OneToOneField("finance.Balance", null=True, related_name="payment")

    # null=True because field did not exist for Qantani payments
    mollie_id = models.CharField(max_length=255, null=True)

    succeeded = models.BooleanField(default=False, help_text="Payment was validated by PSP")

    # Obsolete but contain possible relevant information
    qantani_transaction_id = models.IntegerField(null=True)
    qantani_transaction_code = models.CharField(max_length=255, null=True)

    def create_and_link_credit(self):
        """
        Create user's credit following a successful payment
        Returns newly created Balance object
        """
        if not self.balance:
            self.balance = Balance.objects.create(user=self.order.user, type="CR", amount=self.amount,
                                                  notes="iDeal betaling voor bestelling #%d" % self.order.pk)
            self.save()
        return self.balance

    def __unicode__(self):
        status = "Succeeded" if self.succeeded else "Failed"
        return "%s payment of E%s by %s" % (status, self.amount, self.order.user)


class BalanceManager(models.Manager):
    """
    Implements:
      * vokouser.balance.credit()
      * vokouser.balance.debit()
    """
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


class Balance(TimeStampedModel):
    """
    Represents a transaction. Perhaps 'Transaction' would be a better name for this class (FIXME)
    Examples of transactions: iDeal payment, order debit, gas compensation, order correction, etc.
    A transaction is either debit (DR) or credit (CR).
    """
    TYPES = (
        ("CR", "Credit"),
        ("DR", "Debit"),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="balance")
    type = models.CharField(max_length=2, choices=TYPES, db_index=True)
    amount = models.DecimalField(max_digits=6, decimal_places=2)
    notes = models.TextField()

    def __unicode__(self):
        return u"[%s] %s: %s" % (self.user, self.type, self.amount)

    def save(self, *args, **kwargs):
        """ Sanity check, the amount may not be zero or less. """
        if self.amount <= 0:
            raise ValueError("Amount may not be zero or negative. Amount was: %s" % self.amount)
        super(Balance, self).save(*args, **kwargs)

    objects = BalanceManager()
