from django.db import models
from shared.models import Address


class Supplier(models.Model):
    name = models.CharField(max_length=255)
    address = models.ForeignKey(Address)


class OrderRound(models.Model):
    # orders open from <date> to <date>
    # open to suppliers from <date> to <date>
    open_from = models.DateField()


class Order(models.Model):
    products = models.ManyToManyField("Product", through="OrderProduct")
    order_round = models.ForeignKey("OrderRound")


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

    unit_of_measurement = models.CharField(max_length=2, choices=UNITS)
    price_in_cents = models.IntegerField()

    supplier = models.ForeignKey("Supplier")
    # When linked to OrderRound, product is valid until order round ends. Otherwise, valid indefinitely
    order_round = models.ForeignKey("OrderProduct", null=True, related_name="TODO")


class SupplierOrderProduct(models.Model):
    order = models.ForeignKey("SupplierOrder")
    product = models.ForeignKey("Product")
    amount = models.IntegerField()


class SupplierOrder(models.Model):
    products = models.ManyToManyField("Product", through="SupplierOrderProduct")
    order_round = models.ForeignKey("OrderRound")  # <-- maybe not required