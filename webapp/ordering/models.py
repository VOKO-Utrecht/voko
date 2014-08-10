from decimal import Decimal, ROUND_UP
from django.db import models
from accounts.models import Address
from finance.models import Payment, Balance
from vokou import settings

# TODO use TimeStampedModel for all models
# TODO: use slugs in relevant models (product, supplier, etc)


class Supplier(models.Model):
    name = models.CharField(max_length=50, unique=True)
    address = models.ForeignKey(Address)

    def __unicode__(self):
        return self.name


class OrderRound(models.Model):
    open_for_orders = models.DateField()
    closed_for_orders = models.DateField()
    collect_date = models.DateField()
    # TODO: Set default values to the values of previous object
    markup_percentage = models.DecimalField(decimal_places=2, max_digits=5, default=5.0)
    transaction_costs = models.DecimalField(decimal_places=2, max_digits=5, default=0.35)

    def __unicode__(self):
        return "Order round %d" % self.id


class Order(models.Model):
    """ Order order: ;)
    1. create order (this is implicit even)
    2. place/confirm order (make it definitive for payment)
    3. pay/finalize order
    4. collect order
    """

    products = models.ManyToManyField("Product", through="OrderProduct")
    order_round = models.ForeignKey("OrderRound")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="orders")

    # This might have to change to 'paid' or something
    finalized = models.BooleanField(default=False)  # TODO remove?
    payment = models.OneToOneField(Payment, blank=True, null=True)
    # Whether the order has been retrieved by the user
    collected = models.BooleanField(default=False)

    debit = models.OneToOneField(Balance, null=True, blank=True)

    def __unicode__(self):
        return "Order %d; value: E%s; user: %s" % (self.id, self.total_price, self.user)

    @property
    def total_price(self):
        product_sum = sum([p.total_price for p in self.orderproduct_set.all()])
        return product_sum + self.order_round.transaction_costs + self.member_fee

    @property
    def member_fee(self):
        # Add contribution if this is users' first order (unfinished orders not included)
        non_finalized_orders = self.user.orders.filter(finalized=True)
        total = len(non_finalized_orders)
        if self.pk:
            if self in non_finalized_orders:
                total -= 1
        if total == 0:
            return Decimal(settings.MEMBER_FEE)
        return Decimal(0)

    def place_order_and_debit(self):
        debit = Balance.objects.create(user=self.user,
                                       type="DR",
                                       amount=self.total_price,
                                       notes="Debit of %s for Order %d" % (self.total_price, self.pk))
        self.debit = debit

    def create_and_add_payment(self):
        to_pay = self.user.balance.debit()
        # Sanity check.  TODO: Allow orders without payment when credits exceed total order price.
        assert(to_pay > 0, "Debit is negative.")
        self.payment = Payment.objects.create(amount=to_pay)


class OrderProduct(models.Model):
    order = models.ForeignKey("Order")
    product = models.ForeignKey("Product")
    amount = models.IntegerField()
    # created at etc

    def __unicode__(self):
        return "%d x %s" % (self.amount, self.product)

    @property
    def total_price(self):
        return self.amount * self.product.retail_price


class OrderProductCorrection(models.Model):
    order_product = models.OneToOneField("OrderProduct")
    supplied_amount = models.DecimalField(max_digits=6, decimal_places=1)
    notes = models.TextField(blank=True)
    credit = models.OneToOneField(Balance)

    def __unicode__(self):
        return "Correction on OrderProduct: %s" % self.order_product

    def calculate_refund(self):
        before_correction = self.order_product.total_price
        new_price = self.supplied_amount * self.order_product.product.retail_price
        return (before_correction - new_price) - self.credit_used


class Product(models.Model):
    UNITS = (
        ('St', 'Stuk'),
        ('G',  'Gram'),
        ('KG', 'Kilogram'),
        ('P',  'Pond'),
        ('L',  'Liter'),
    )

    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    unit_of_measurement = models.CharField(max_length=2, choices=UNITS)
    base_price = models.DecimalField(max_digits=6, decimal_places=2)
    supplier = models.ForeignKey("Supplier")
    order_round = models.ForeignKey("OrderRound", related_name="products")

    minimum_total_order = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return '"%s" van "%s"' % (self.name, self.supplier)

    @property
    def retail_price(self):
        total_percentage = 100 + self.order_round.markup_percentage
        new_price = (self.base_price / 100) * total_percentage
        rounded = new_price.quantize(Decimal('.01'), rounding=ROUND_UP)
        return rounded


class SupplierOrderProduct(models.Model):
    order = models.ForeignKey("SupplierOrder")
    product = models.ForeignKey("Product")
    amount = models.IntegerField()


class SupplierOrder(models.Model):
    products = models.ManyToManyField("Product", through="SupplierOrderProduct")
    order_round = models.ForeignKey("OrderRound")  # <-- maybe not required