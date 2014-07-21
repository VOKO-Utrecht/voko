from django.db import models
from accounts.models import Address
from vokou import settings

# TODO use TimeStampedModel for all models

class Supplier(models.Model):
    name = models.CharField(max_length=50, unique=True)
    address = models.ForeignKey(Address)

    def __unicode__(self):
        return self.name


class OrderRound(models.Model):
    # orders open from <date> to <date>
    # open to suppliers from <date> to <date>
    open_for_orders = models.DateField()
    closed_for_orders = models.DateField()
    collect_date = models.DateField()

    def __unicode__(self):
        return "Order round %d" % self.id


class Order(models.Model):
    products = models.ManyToManyField("Product", through="OrderProduct")
    order_round = models.ForeignKey("OrderRound")
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    def __unicode__(self):
        return "Order %d" % self.id


class OrderProduct(models.Model):
    order = models.ForeignKey("Order")
    product = models.ForeignKey("Product")
    amount = models.IntegerField()
    # created at etc


class Product(models.Model):
    UNITS = (
        ('St', 'Stuk'),
        ('G',  'Gram'),
        ('KG', 'Kilogram'),
        ('P',  'Pond'),
        ('L',  'Liter'),
    )

    name = models.CharField(max_length=50)
    description = models.TextField()
    unit_of_measurement = models.CharField(max_length=2, choices=UNITS)
    price_in_cents = models.IntegerField()

    supplier = models.ForeignKey("Supplier")
    order_round = models.ForeignKey("OrderRound", related_name="products")

    minimum_total_order = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return '"%s" van "%s"' % (self.name, self.supplier)

class SupplierOrderProduct(models.Model):
    order = models.ForeignKey("SupplierOrder")
    product = models.ForeignKey("Product")
    amount = models.IntegerField()


class SupplierOrder(models.Model):
    products = models.ManyToManyField("Product", through="SupplierOrderProduct")
    order_round = models.ForeignKey("OrderRound")  # <-- maybe not required