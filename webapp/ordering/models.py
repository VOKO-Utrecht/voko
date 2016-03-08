# -*- coding: utf-8 -*-
from jsonfield import JSONField

import pytz
from datetime import datetime
from decimal import Decimal, ROUND_UP, ROUND_DOWN
from django.db import models
from django_extensions.db.models import TimeStampedModel
from accounts.models import Address
from finance.models import Balance
from log import log_event
from mailing.helpers import mail_user, get_template_by_id, render_mail_template
from ordering.core import get_or_create_order, get_current_order_round, find_unit
from django.conf import settings

ORDER_CONFIRM_MAIL_ID = 12
ORDER_FAILED_ID = 37


class Supplier(TimeStampedModel):
    class Meta:
        verbose_name = "Leverancier"

    name = models.CharField(max_length=50, unique=True)
    address = models.ForeignKey(Address)
    email = models.EmailField()
    biography = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    facebook_url = models.URLField(blank=True, null=True)

    def __unicode__(self):
        return self.name

    def has_orders_in_current_order_round(self):
        return OrderProduct.objects.filter(product__supplier=self,
                                           order__order_round=get_current_order_round(),
                                           order__paid=True).exists()


class OrderRound(TimeStampedModel):
    class Meta:
        verbose_name = "Bestelronde"
        verbose_name_plural = "Bestelronden"

    open_for_orders = models.DateTimeField()
    closed_for_orders = models.DateTimeField()
    collect_datetime = models.DateTimeField()
    # TODO: Set default values to the values of previous object
    markup_percentage = models.DecimalField(decimal_places=2, max_digits=5, default=7.0)
    transaction_costs = models.DecimalField(decimal_places=2, max_digits=5, default=0.42)
    order_placed = models.BooleanField(default=False, editable=False)

    def is_not_open_yet(self):
        current_datetime = datetime.now(pytz.utc)  # Yes, UTC. see Django's timezone docs
        return current_datetime < self.open_for_orders

    def is_over(self):
        ## over, past, expired
        current_datetime = datetime.now(pytz.utc)  # Yes, UTC. see Django's timezone docs
        print current_datetime
        print self.closed_for_orders
        return current_datetime > self.closed_for_orders

    @property
    def is_open(self):
        current_datetime = datetime.now(pytz.utc)  # Yes, UTC. see Django's timezone docs
        return current_datetime >= self.open_for_orders and current_datetime < self.closed_for_orders

    def is_current(self):
        return self == get_current_order_round()

    def suppliers(self):
        """
        Return suppliers with at least one paid order in this round
        """
        supplier_ids = set(OrderProduct.objects.filter(order__order_round=self,
                                                       order__paid=True).values_list(
            'product__supplier', flat=True))

        return [Supplier.objects.get(id=supplier_id) for supplier_id in supplier_ids]

    def total_order_amount_per_supplier(self, supplier):
        """
        Return a dict with total order amount (in euro) for a supplier
        """
        order_products = OrderProduct.objects.filter(order__order_round=self, order__paid=True,
                                                     product__supplier=supplier)
        total = sum([o_p.total_cost_price() for o_p in order_products])
        return total

    def total_order_amount(self):
        order_products = OrderProduct.objects.filter(order__order_round=self, order__paid=True)
        total = sum([o_p.total_cost_price() for o_p in order_products])
        return total

    def total_corrections(self):
        corrections = OrderProductCorrection.objects.filter(order_product__order__order_round=self)
        return {'supplier_exc': sum([c.calculate_supplier_refund() for c in corrections.filter(charge_supplier=True)]),
                'supplier_inc': sum([c.calculate_refund() for c in corrections.filter(charge_supplier=True)]),
                'voko_inc': sum([c.calculate_refund() for c in corrections.filter(charge_supplier=False)])}

    def to_pay(self):
        return self.total_order_amount() - self.total_corrections()['supplier_exc']

    def total_profit(self):
        orderproducts = OrderProduct.objects.filter(order__order_round=self, order__paid=True)
        return sum([orderprod.product.profit for orderprod in orderproducts])

    def __unicode__(self):
        return "Bestelronde #%s" % self.pk


class OrderManager(models.Manager):
    use_for_related_fields = True

    def get_current_order(self):
        try:
            return super(OrderManager, self).get_queryset().filter(paid=False,
                                                                   user=self.instance,
                                                                   order_round=get_current_order_round()).order_by('-pk')[0]
        except IndexError:
            return get_or_create_order(user=self.instance)

    def get_last_paid_order(self):
        return super(OrderManager, self).get_queryset().filter(paid=True,
                                                               user=self.instance,
                                                               order_round=get_current_order_round()).order_by('-pk')[0]


class Order(TimeStampedModel):
    """ Order order: ;)
    1. create order (this is implicit even)
    2. place/confirm order (make it definitive for payment)
    3. pay/finalize order
    4. collect order
    """

    class Meta:
        verbose_name = "Bestelling"
        verbose_name_plural = "Bestellingen"

    objects = OrderManager()

    products = models.ManyToManyField("Product", through="OrderProduct")
    order_round = models.ForeignKey("OrderRound", related_name="orders")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="orders")
    user_notes = models.TextField(null=True, blank=True)

    finalized = models.BooleanField(default=False)  # To "freeze" order before payment
    paid = models.BooleanField(default=False)  # True when paid
    # Debit created when this order was finished (describes total order value)
    debit = models.OneToOneField(Balance, null=True, blank=True, related_name="order")

    # TODO: order cannot be 'paid' without having a 'debit'. Add sanity check.

    def __unicode__(self):
        return u"Order %d; user: %s" % (self.id, self.user)

    @property
    def has_products(self):
        return len(self.orderproducts.all()) > 0

    @property
    def total_price(self):
        product_sum = sum([p.total_retail_price for p in self.orderproducts.all()])
        return product_sum + self.order_round.transaction_costs + self.member_fee

    def total_price_to_pay_with_balances_taken_into_account(self):
        if self.user.balance.credit() > 0:
            total_price = self.total_price - self.user.balance.credit()
            return total_price if total_price > 0 else 0

        if self.user.balance.debit() > 0:
            return self.total_price + self.user.balance.debit()

        return self.total_price

    @property
    def member_fee(self):
        # Return contribution fee if this is users' first order (unfinished orders not included)
        amount_of_paid_orders = self.user.orders.\
            filter(paid=True).\
            exclude(pk=self.pk).\
            exclude(pk__gt=self.pk).\
            count()

        if amount_of_paid_orders == 0:
            return Decimal(settings.MEMBER_FEE)

        return Decimal(0)

    @property
    def user_order_id(self):
        user_orders = self.user.orders.exclude(orderproducts=None).order_by("pk")
        for index, uo in enumerate(user_orders):
            if uo == self:
                return index + 1

    def complete_after_payment(self):
        log_event(event="Completing (paid) order %s" % self.id, user=self.user)
        self.paid = True
        self.save()
        self.create_debit()
        self.mail_confirmation()

    def create_debit(self):
        """
        Create debit for order and create one-to-one relation
        """
        log_event(event="Creating debit for order %s" % self.id)
        self.debit = Balance.objects.create(user=self.user,
                                            type="DR",
                                            amount=self.total_price,
                                            notes="Debit van %s voor bestelling #%d" % (self.total_price, self.pk))
        self.save()

    def mail_confirmation(self):
        mail_template = get_template_by_id(ORDER_CONFIRM_MAIL_ID)
        rendered_template_vars = render_mail_template(mail_template, user=self.user, order=self)
        mail_user(self.user, *rendered_template_vars)

    def mail_failure_notification(self):
        """
        When order was paid after round has closed (corner case)
        """
        mail_template = get_template_by_id(ORDER_FAILED_ID)
        rendered_template_vars = render_mail_template(mail_template, user=self.user, order=self)
        mail_user(self.user, *rendered_template_vars)


class OrderProduct(TimeStampedModel):
    class Meta:
        verbose_name = "Productbestelling"
        verbose_name_plural = "Productbestellingen"
        unique_together = ('order', 'product')

    order = models.ForeignKey("Order", related_name="orderproducts")
    product = models.ForeignKey("Product", related_name="orderproducts")
    amount = models.IntegerField(verbose_name="Aantal")

    def __unicode__(self):
        return u"%d x %s" % (self.amount, self.product)

    @property
    def total_retail_price(self):
        return self.amount * self.product.retail_price

    def total_cost_price(self):
        return self.amount * self.product.base_price


class CorrectionQuerySet(models.query.QuerySet):
    def delete(self):
        #  OneToOne relation isn't cascaded in this direction :(
        for obj in self:
            obj.credit.delete()
        return super(CorrectionQuerySet, self).delete()


class CorrectionManager(models.Manager):
    def get_queryset(self):
        return CorrectionQuerySet(self.model, using=self._db)


class OrderProductCorrection(TimeStampedModel):
    objects = CorrectionManager()

    class Meta:
        verbose_name = "Productbestelling-correctie"
        verbose_name_plural = "Productbestelling-correcties"

    order_product = models.OneToOneField("OrderProduct", related_name="correction")
    supplied_percentage = models.IntegerField()
    notes = models.TextField(blank=True)
    credit = models.OneToOneField(Balance, related_name="correction")
    charge_supplier = models.BooleanField(default=True, verbose_name="Charge expenses to supplier")

    def __unicode__(self):
        return u"Correction on OrderProduct: %s" % self.order_product

    def calculate_refund(self):
        """ rounded member refund """
        return Decimal((self.order_product.total_retail_price / 100) * (100 - self.supplied_percentage))\
            .quantize(Decimal('.01'), rounding=ROUND_DOWN)

    def calculate_supplier_refund(self):
        return Decimal((self.order_product.total_cost_price() / 100) * (100 - self.supplied_percentage))\
            .quantize(Decimal('.01'), rounding=ROUND_DOWN)

    def _create_credit(self):
        return Balance.objects.create(user=self.order_product.order.user,
                                      type="CR",
                                      amount=self.calculate_refund(),
                                      notes="Correctie in ronde %d, %dx %s, geleverd: %s%%" %
                                            (self.order_product.product.order_round.id,
                                             self.order_product.amount,
                                             self.order_product.product.name,
                                             self.supplied_percentage))

    def save(self, *args, **kwargs):
        if self.pk is None:
            self.credit = self._create_credit()
        super(OrderProductCorrection, self).save(*args, **kwargs)


class ProductCategory(TimeStampedModel):
    class Meta:
        verbose_name = "Productcategorie"
        verbose_name_plural = "Productcategorieën"

    name = models.CharField(max_length=100)

    def __unicode__(self):
        return self.name


class ProductUnit(TimeStampedModel):
    class Meta:
        verbose_name = "Producteenheid"
        verbose_name_plural = "Producteenheden"

    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255)
    abbreviations = models.CharField(max_length=255, blank=True, help_text="whitespace separated")

    def __unicode__(self):
        return self.description


class Product(TimeStampedModel):
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Producten"

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    unit = models.ForeignKey(ProductUnit, null=True)
    unit_amount = models.IntegerField(default=1, help_text="e.g. if half a kilo: \"500\"")
    base_price = models.DecimalField(max_digits=6, decimal_places=2)
    supplier = models.ForeignKey("Supplier", related_name="products")
    order_round = models.ForeignKey("OrderRound", related_name="products")
    category = models.ForeignKey("ProductCategory", related_name="products", null=True, blank=True)
    new = models.BooleanField(default=False, verbose_name="Show 'new' label")

    maximum_total_order = models.IntegerField(null=True, blank=True)

    def __unicode__(self):
        return u'[ronde %s] %s (%s)' % (self.order_round.pk, self.name, self.supplier)

    @property
    def unit_of_measurement(self):
        return "%s %s" % (self.unit_amount, self.unit.description.lower())

    @property
    def profit(self):
        return self.retail_price - self.base_price

    @property
    def retail_price(self):
        total_percentage = 100 + self.order_round.markup_percentage
        new_price = (self.base_price / 100) * total_percentage
        rounded = new_price.quantize(Decimal('.01'), rounding=ROUND_UP)
        return rounded

    @property
    def amount_available(self):
        if self.maximum_total_order is None:
            return
        maximum = self.maximum_total_order
        total = self.amount_ordered
        return maximum - total

    @property
    def amount_ordered(self):
        orderproducts = self.orderproducts.filter(order__paid=True)
        total = sum(op.amount for op in orderproducts)
        return total

    @property
    def percentage_available_of_max(self):
        if self.maximum_total_order is None:
            return 100
        return int((float(self.amount_available) / float(self.maximum_total_order)) * 100)

    @property
    def is_available(self):
        if self.maximum_total_order is None:
            return True
        return self.amount_available > 0

    def create_corrections(self):
        for order_product in self.orderproducts.filter(correction__isnull=True, order__paid=True):
            OrderProductCorrection.objects.create(
                order_product=order_product,
                supplied_percentage=0,
                notes='Product niet geleverd: "%s" (%s) [%s]' % (self.name, self.supplier.name, self.id),
                charge_supplier=True,
            )

    def determine_if_product_is_new_and_set_label(self):
        try:
            prev_round = OrderRound.objects.get(id=self.order_round.id-1)
        except OrderRound.ObjectDoesNotExist:
            return

        if not prev_round.products.filter(name=self.name,
                                          description=self.description,
                                          supplier=self.supplier,
                                          unit=self.unit):
            self.new = True
            self.save()
            log_event(event="Setting product %s to 'new' because I could not find a "
                            "similar product in order round %d" % (self, prev_round.id))


class DraftProduct(TimeStampedModel):
    data = JSONField()
    supplier = models.ForeignKey(Supplier)
    order_round = models.ForeignKey(OrderRound)
    is_valid = models.BooleanField(default=False)
    validation_error = models.CharField(max_length=255, blank=True, null=True)

    def __unicode__(self):
        return u"[%d] Draft Product [%s]" % (self.id, self.data)

    def validate(self):
        self.is_valid = False
        if not self._valid_name(self.data['name']):
            self.validation_error = "Naam onjuist"
        elif not self._valid_price(self.data['base_price']):
            self.validation_error = "Prijs onjuist"
        elif not self._valid_unit(self.data['unit']):
            self.validation_error = "Eenheid onjuist"
        elif not self._valid_max(self.data['maximum_total_order']):
            self.validation_error = "Max. onjuist"
        else:
            self.is_valid = True
            self.validation_error = None
        self.save()

    def _valid_name(self, name):
        try:
            return len(name) > 0
        except (ValueError, TypeError):
            return False

    def _valid_price(self, price):
        try:
            float(price)
            return True
        except (ValueError, TypeError):
            return False

    def _valid_unit(self, unit):
        try:
            find_unit(unit)
            return True
        except (RuntimeError, TypeError):
            return False

    def _valid_max(self, max):
        try:
            return max is None or (int(max) and max > 0)
        except ValueError:
            return False

    def create_product(self):
        if not self.is_valid:
            return

        # Decide on unit & amount
        unit = self.data['unit']
        unit_amount, unit = find_unit(unit)

        prod = Product.objects.create(
            name=self.data['name'],
            description=self.data['description'] if self.data['description'] else "",
            unit=unit,
            unit_amount=unit_amount,
            base_price=self.data['base_price'],
            maximum_total_order=self.data['maximum_total_order'],
            supplier=self.supplier,
            order_round=self.order_round,
        )

        if self.data['category']:
            try:
                prod.category = ProductCategory.objects.get(name=self.data['category'])
                prod.save()
            except ProductCategory.DoesNotExist:
                pass

        return prod

    @property
    def product_data(self):
        return self.data['product_data']
