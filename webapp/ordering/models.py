# -*- coding: utf-8 -*-
from jsonfield import JSONField

import pytz
from datetime import datetime
from decimal import Decimal, ROUND_UP, ROUND_DOWN
from django.db import models, transaction
from django_extensions.db.models import TimeStampedModel
from django.core.exceptions import ValidationError
from accounts.models import Address, VokoUser
from finance.models import Balance
from log import log_event
from mailing.helpers import mail_user, get_template_by_id, render_mail_template
from ordering.core import get_or_create_order, get_current_order_round, find_unit
from django.conf import settings
from constance import config

from agenda.models import TransientEvent


class Supplier(TimeStampedModel):
    class Meta:
        verbose_name = "Leverancier"

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    address = models.ForeignKey(Address, on_delete=models.CASCADE)
    contact_person = models.CharField(max_length=50, blank=True)
    email = models.EmailField()
    phone_number = models.CharField(max_length=25, blank=True)
    biography = models.TextField(blank=True, null=True)
    transport_info = models.TextField(blank=True, null=True)
    website = models.URLField(blank=True, null=True)
    facebook_url = models.URLField(blank=True, null=True)

    def __str__(self):
        return self.name

    def has_orders_in_current_order_round(self):
        """
        Ignores stock products!
        """
        return OrderProduct.objects.filter(
            product__supplier=self,
            order__order_round=get_current_order_round(),
            order__paid=True,
        ).exists()


class PickupLocation(TimeStampedModel):
    """
    Pickup Location for an order round
    """

    class Meta:
        verbose_name = "Ophaallocatie"

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255)
    address = models.ForeignKey(
        Address, null=True, blank=True, on_delete=models.CASCADE
    )
    is_default = models.BooleanField(default=False)

    def save(self, **kwargs):
        if self.is_default:
            # make all other locations non-default
            PickupLocation.objects.update(is_default=False)
        super(PickupLocation, self).save(**kwargs)

    def __str__(self):
        return self.name


class OrderRound(TimeStampedModel):
    class Meta:
        verbose_name = "Bestelronde"
        verbose_name_plural = "Bestelronden"

    id = models.AutoField(primary_key=True)
    open_for_orders = models.DateTimeField(help_text="When this order round will open")
    closed_for_orders = models.DateTimeField(
        help_text="When this order round will close"
    )
    collect_datetime = models.DateTimeField(
        help_text="When the products can be collected"
    )
    markup_percentage = models.DecimalField(
        decimal_places=2, max_digits=5, default=config.MARKUP_PERCENTAGE
    )
    transaction_costs = models.DecimalField(
        decimal_places=2, max_digits=5, default=0.21
    )
    order_placed = models.BooleanField(
        default=False,
        editable=False,
        help_text="Whether the order was placed at our suppliers",
    )

    reminder_hours_before_closing = models.IntegerField(
        default=12,
        help_text="Number of hours before closing time when order "
        "reminder mail will be sent",
    )
    reminder_sent = models.BooleanField(
        default=False,
        editable=False,
        help_text="Whether we've sent order reminders to our members",
    )
    reminder_hours_before_pickup = models.IntegerField(
        default=4,
        help_text="Number of hours before collecting time when pickup "
        "reminder mail will be sent",
    )
    pickup_reminder_sent = models.BooleanField(
        default=False,
        editable=False,
        help_text="Whether we've sent pickup order reminders to our members",
    )
    rides_mails_sent = models.BooleanField(
        default=False, editable=False, help_text="Whether we've sent ride info mails"
    )
    prepare_ride_mails_sent = models.BooleanField(
        default=False,
        editable=False,
        help_text="Whether we've sent prepare ride info mails",
    )
    ridecosts_request_mails_sent = models.BooleanField(
        default=False,
        editable=False,
        help_text="Whether we've sent ridecosts request mails",
    )
    distribution_mails_sent = models.BooleanField(
        default=False,
        editable=False,
        help_text="Whether we've sent distribution info mails",
    )

    distribution_coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coordinating_distribution_orderrounds",
    )

    transport_coordinator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coordinating_transport_orderrounds",
    )

    pickup_location = models.ForeignKey(
        PickupLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    def clean(self):
        if self.is_over:
            raise ValidationError(
                "Orderrounds which are in the past cannot be saved or changed"
            )

    def is_not_open_yet(self):
        current_datetime = datetime.now(pytz.utc)
        return current_datetime < self.open_for_orders

    @property
    def is_over(self):
        # Over, past, expired
        current_datetime = datetime.now(pytz.utc)
        return current_datetime > self.closed_for_orders

    @property
    def is_open(self):
        current_datetime = datetime.now(pytz.utc)
        return (
            current_datetime >= self.open_for_orders
            and current_datetime < self.closed_for_orders
        )

    def is_current(self):
        return self == get_current_order_round()

    def get_next_order_round(self):
        order_rounds = OrderRound.objects.all()
        return (
            order_rounds.filter(open_for_orders__gt=self.open_for_orders)
            .order_by("open_for_orders")
            .first()
        )

    def get_previous_order_round(self):
        order_rounds = OrderRound.objects.all()
        return (
            order_rounds.filter(open_for_orders__lt=self.open_for_orders)
            .order_by("open_for_orders")
            .reverse()
            .first()
        )

    def suppliers(self):
        """
        Return suppliers with at least one paid order in this round
        """
        supplier_ids = set(
            OrderProduct.objects.filter(
                order__order_round=self, order__paid=True
            ).values_list("product__supplier", flat=True)
        )

        return [Supplier.objects.get(id=supplier_id) for supplier_id in supplier_ids]

    def supplier_total_order_sum(self, supplier):
        """
        Return sum of total order amount (in euro) for a supplier
        """
        order_products = OrderProduct.objects.filter(
            order__order_round=self, order__paid=True, product__supplier=supplier
        )
        return sum([o_p.total_cost_price() for o_p in order_products])

    def total_order_sum(self):
        order_products = OrderProduct.objects.filter(
            order__order_round=self, order__paid=True
        )
        return sum([o_p.total_cost_price() for o_p in order_products])

    def total_corrections(self):
        """
        supplier_exc:   Total supplier refund (product cost prices)
                        to be paid by suppliers
        supplier_inc:   Total member refund (product retail prices) ...
        voko_inc:       Total member refund to be paid by VOKO
                        (e.g. lost/broken products)
        """
        corrections = OrderProductCorrection.objects.filter(
            order_product__order__order_round=self
        )

        supplier_exc = sum(
            [
                c.calculate_supplier_refund()
                for c in corrections.filter(charge_supplier=True)
            ]
        )

        supplier_inc = sum(
            [c.calculate_refund() for c in corrections.filter(charge_supplier=True)]
        )

        voko_inc = sum(
            [c.calculate_refund() for c in corrections.filter(charge_supplier=False)]
        )

        return {
            "supplier_exc": supplier_exc,
            "supplier_inc": supplier_inc,
            "voko_inc": voko_inc,
        }

    def total_profit(self):
        """
        Total profit purely by markup on products for this round
        """
        # FIXME: Does not take corrections into account. Is this by design?
        orderproducts = OrderProduct.objects.filter(
            order__order_round=self, order__paid=True
        )
        return sum(
            [orderprod.product.profit * orderprod.amount for orderprod in orderproducts]
        )

    def total_revenue(self):
        """
        Total revenue on products for this round
        """
        order_products = OrderProduct.objects.filter(
            order__order_round=self, order__paid=True
        )

        total = sum([o_p.total_retail_price for o_p in order_products])
        print("  total_revenue: %f" % total)
        return total

    def number_of_orders(self):
        """
        Return the total number of paid orders
        """
        return self.paid_orders.count()

    @property
    def paid_orders(self):
        return self.orders.filter(paid=True)

    @property
    def orders_per_supplier(self):
        data = {}
        for supplier in Supplier.objects.all():
            suppliers_products_this_round = supplier.products.filter(order_round=self)
            data[supplier] = {
                "orderproducts": [],
                "sum": self.supplier_total_order_sum(supplier),
            }

            for product in suppliers_products_this_round:
                order_products = product.orderproducts.filter(order__paid=True)
                product_sum = sum([op.amount for op in order_products])
                if product_sum == 0:
                    continue
                data[supplier]["orderproducts"].append(
                    {
                        "product": product,
                        "amount": product_sum,
                        "sub_total": product_sum * product.base_price,
                    }
                )

        return data

    def days_since_collection(self):
        """
        Return days sincs collection date
        """
        return (datetime.now(tz=pytz.UTC) - self.collect_datetime).days

    def get_users_without_orders(self):
        def _users_without_orders_filter(voko_user):
            return not Order.objects.filter(
                order_round=self, user=voko_user, paid=True
            ).exists()

        return list(
            filter(
                _users_without_orders_filter, VokoUser.objects.filter(is_active=True)
            )
        )

    def get_users_with_orders(self):
        def _users_with_orders_filter(voko_user):
            return Order.objects.filter(
                order_round=self, user=voko_user, paid=True
            ).exists()

        return list(
            filter(_users_with_orders_filter, VokoUser.objects.filter(is_active=True))
        )

    def send_reminder_mails(self):
        """
        Sends reminder mails for users not yet ordered this round
        """
        if self.reminder_sent is True:
            log_event(
                event="Not sending order reminder for round %d because "
                "reminder_sent is True" % self.pk
            )

            return

        log_event(event="Sending order reminder for round %d" % self.pk)

        mail_template = get_template_by_id(config.ORDER_REMINDER_MAIL)

        self.reminder_sent = True
        self.save()

        for user in self.get_users_without_orders():
            rendered_template_vars = render_mail_template(
                mail_template, user=user, order_round=self
            )
            mail_user(user, *rendered_template_vars)

    def send_pickup_reminder_mails(self):
        """
        Sends pickup reminder mails for users who did order this round
        """
        if self.pickup_reminder_sent is True:
            log_event(
                event="Not sending pickup reminder for round %d because "
                "pickup_reminder_sent is True" % self.pk
            )
            return

        log_event(event="Sending pickup reminder for round %d" % self.pk)

        mail_template = get_template_by_id(config.PICKUP_REMINDER_MAIL)

        self.pickup_reminder_sent = True
        self.save()

        for user in self.get_users_with_orders():
            rendered_template_vars = render_mail_template(
                mail_template, user=user, order_round=self
            )
            mail_user(user, *rendered_template_vars)

    def send_ride_mails(self):
        if self.rides_mails_sent is True:
            log_event(
                event="Not sending ride mails for round %d because "
                "rides_mails_sent is True" % self.pk
            )
            return

        log_event(event="Sending ride mails for round %d" % self.pk)

        mail_template = get_template_by_id(config.RIDE_MAIL)

        self.rides_mails_sent = True
        self.save()

        rides = self.rides.all()
        for ride in rides:
            involved = {ride.driver, ride.codriver, self.distribution_coordinator}
            for user in involved:
                if user is None:
                    continue
                rendered_template_vars = render_mail_template(
                    mail_template,
                    user=user,
                    ride=ride,
                    order_round=self,
                    base_url=settings.BASE_URL,
                )
                mail_user(user, *rendered_template_vars)

    def send_prepare_ride_mails(self):
        if self.prepare_ride_mails_sent is True:
            log_event(
                event="Not sending prepare ride mails for round %d "
                "because prepare_ride_mails_sent is True" % self.pk
            )
            return

        log_event(event="Sending prepare ride mails for round %d" % self.pk)

        mail_template = get_template_by_id(config.PREPARE_RIDE_MAIL)

        self.prepare_ride_mails_sent = True
        self.save()

        rides = self.rides.all()
        for ride in rides:
            drivers = [ride.driver, ride.codriver]
            for user in drivers:
                rendered_template_vars = render_mail_template(
                    mail_template, user=user, ride=ride, base_url=settings.BASE_URL
                )
                mail_user(user, *rendered_template_vars)

    def send_ridecosts_request_mails(self):
        if self.ridecosts_request_mails_sent is True:
            log_event(
                event="Not sending ridecosts mails for round %d "
                "because ridecosts_request_mails_sent is True" % self.pk
            )
            return

        log_event(event="Sending ridecosts reqst mails for round %d" % self.pk)

        mail_template = get_template_by_id(config.RIDECOSTS_REQUEST_MAIL)

        self.ridecosts_request_mails_sent = True
        self.save()

        rides = self.rides.all()
        for ride in rides:
            drivers = [ride.driver]
            for user in drivers:
                rendered_template_vars = render_mail_template(
                    mail_template, user=user, ride=ride, base_url=settings.BASE_URL
                )
                mail_user(user, *rendered_template_vars)

    def send_distribution_mails(self):
        if self.distribution_mails_sent is True:
            log_event(
                event="Not sending distribution mails for round %d "
                "because distribution_mails_sent is True" % self.pk
            )
            return

        log_event(event="Sending distribution mails for round %d" % self.pk)

        mail_template = get_template_by_id(config.DISTRIBUTION_MAIL)

        self.distribution_mails_sent = True
        self.save()

        shifts = self.distribution_shifts.all()
        for shift in shifts:
            for user in shift.members.all():
                rendered_template_vars = render_mail_template(
                    mail_template, user=user, shift=shift, base_url=settings.BASE_URL
                )
                mail_user(user, *rendered_template_vars)

    def get_pickup_location(self):
        if self.pickup_location is not None:
            return self.pickup_location
        return PickupLocation.objects.get(is_default=True)

    def as_event(self):
        event = TransientEvent()
        event.address = self.pickup_location.address
        event.title = f"Bestelronde {self.id} - {self.pickup_location}"
        # event.short_description = F"Bestelronde {self.id}"
        event.date = self.open_for_orders.date()
        event.time = self.open_for_orders.time()
        return event

    def __str__(self):
        return "Bestelronde #%s" % self.pk


class OrderManager(models.Manager):
    use_for_related_fields = True

    def get_current_order(self):
        """
        Allows us to use:
        VokoUser.orders.get_current_order()
        """
        try:
            return (
                super(OrderManager, self)
                .get_queryset()
                .filter(
                    paid=False,
                    user=self.instance,
                    order_round=get_current_order_round(),
                )
                .order_by("-pk")[0]
            )
        except IndexError:
            return get_or_create_order(user=self.instance)

    def get_last_paid_order(self):
        """
        Allows us to use:
        VokoUser.orders.get_last_paid_order()
        """
        try:
            return (
                super(OrderManager, self)
                .get_queryset()
                .filter(
                    paid=True, user=self.instance, order_round=get_current_order_round()
                )
                .order_by("-pk")[0]
            )
        except IndexError:
            return


class Order(TimeStampedModel):
    class Meta:
        verbose_name = "Bestelling"
        verbose_name_plural = "Bestellingen"

    objects = OrderManager()

    id = models.AutoField(primary_key=True)
    products = models.ManyToManyField("Product", through="OrderProduct")
    order_round = models.ForeignKey(
        "OrderRound", related_name="orders", on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, related_name="orders", on_delete=models.CASCADE
    )
    user_notes = models.TextField(null=True, blank=True)

    # To "freeze" order before payment
    finalized = models.BooleanField(default=False)
    paid = models.BooleanField(default=False)
    # Debit created when this order was finished (describes total order value)
    debit = models.OneToOneField(
        Balance, null=True, blank=True, related_name="order", on_delete=models.CASCADE
    )

    # TODO: order cannot be 'paid' without having a 'debit'. Add sanity check.

    def __str__(self):
        return "Order %d; user: %s" % (self.id, self.user)

    @property
    def has_products(self):
        """
        Return if any OrderProducts are created for this order.
        Boolean.
        """
        return bool(self.orderproducts.all())

    @property
    def total_price(self):
        """
        Return total retail price for this order.
        Includes payment transaction costs and eventual member fee.
        """
        product_sum = sum([odp.total_retail_price for odp in self.orderproducts.all()])
        return product_sum + self.order_round.transaction_costs + self.member_fee

    def total_price_to_pay_with_balances_taken_into_account(self):
        """
        Calculate payment amount at the time of the order.
        This amount can be less, equal to or larger than the :total_price:,
        depending on the user's balance (debit or credit).

        Users are forced to repay their debit when placing and order.
        """
        if self.user.balance.credit() > 0:
            total_price = self.total_price - self.user.balance.credit()
            return total_price if total_price > 0 else 0

        if self.user.balance.debit() > 0:
            return self.total_price + self.user.balance.debit()

        return self.total_price

    @property
    def member_fee(self):
        """
        Return contribution fee if this is users'
        first order (non-paid orders not included)
        """
        amount_of_paid_orders = (
            self.user.orders.filter(paid=True)
            .exclude(pk=self.pk)
            .exclude(pk__gt=self.pk)
            .count()
        )

        if amount_of_paid_orders == 0:
            return Decimal(settings.MEMBER_FEE)

        return Decimal(0)

    @property
    def user_order_number(self):
        """
        Counts all user's finished and paid orders, ascending, by ID, and
        returns the number of the current order
        """
        user_orders = self.user.orders.filter(paid=True, finalized=True).order_by("pk")
        for index, uo in enumerate(user_orders):
            if uo == self:
                return index + 1

    def complete_after_payment(self):
        """
        Complete order by setting the 'paid' boolean,
        creating debit and mailing the user.
        """
        log_event(event="Completing (paid) order %s" % self.id, user=self.user)
        with transaction.atomic():
            self.paid = True
            self.save()
            self.create_debit()
        self.mail_confirmation()

    def create_debit(self):
        """
        Create debit for order and create one-to-one relation
        """
        log_event(event="Creating debit for order %s" % self.id)
        self.debit = Balance.objects.create(
            user=self.user,
            type="DR",
            amount=self.total_price,
            notes="Debit van %s voor bestelling #%d" % (self.total_price, self.pk),
        )
        self.save()

    def mail_confirmation(self):
        """
        Send confirmation mail to user about successful order placement
        """
        mail_template = get_template_by_id(config.ORDER_CONFIRM_MAIL)
        rendered_template_vars = render_mail_template(
            mail_template, user=self.user, order=self
        )
        mail_user(self.user, *rendered_template_vars)

    def mail_failure_notification(self):
        """
        Use when order was paid after round has been closed (corner case)
        """
        mail_template = get_template_by_id(config.ORDER_FAILED_MAIL)
        rendered_template_vars = render_mail_template(
            mail_template, user=self.user, order=self
        )
        mail_user(self.user, *rendered_template_vars)


class OrderProduct(TimeStampedModel):
    """
    Represents an order of one particular product
    """

    class Meta:
        verbose_name = "Productbestelling"
        verbose_name_plural = "Productbestellingen"
        unique_together = ("order", "product")

    id = models.AutoField(primary_key=True)
    order = models.ForeignKey(
        "Order", related_name="orderproducts", on_delete=models.CASCADE
    )
    product = models.ForeignKey(
        "Product", related_name="orderproducts", on_delete=models.CASCADE
    )
    amount = models.IntegerField(verbose_name="Aantal")
    retail_price = models.DecimalField(
        max_digits=6, decimal_places=2, help_text="The price the product was sold for"
    )
    base_price = models.DecimalField(
        max_digits=6, decimal_places=2, help_text="The price the product was bought for"
    )

    # TODO: assert order.order_round == product.order_round on save()

    def __str__(self):
        return "%d x %s door %s" % (self.amount, self.product, self.order.user)

    @property
    def total_retail_price(self):
        """
        What the user will pay or paid for this OrderProduct.
        Stored in model as historical record.
        """

        return Decimal(self.amount) * Decimal(str(self.retail_price))

    def total_cost_price(self):
        """
        What VOKO will pay for this product
        """

        return Decimal(self.amount) * Decimal(str(self.base_price))


class CorrectionQuerySet(models.query.QuerySet):
    def delete(self):
        # OneToOne relation isn't cascaded in this direction :(
        # Make sure credit is deleted anyway when correction is deleted
        for obj in self:
            obj.credit.delete()
        return super(CorrectionQuerySet, self).delete()


class CorrectionManager(models.Manager):
    def get_queryset(self):
        return CorrectionQuerySet(self.model, using=self._db)


class OrderProductCorrection(TimeStampedModel):
    """
    Represents a "correction" on an OrderProduct
    Used to register (and compensate for) non/partly delivered products.
    Creates Balance object upon creation.
    """

    objects = CorrectionManager()

    class Meta:
        verbose_name = "Productbestelling-correctie"
        verbose_name_plural = "Productbestelling-correcties"

    id = models.AutoField(primary_key=True)
    order_product = models.OneToOneField(
        "OrderProduct",
        related_name="correction",
        editable=False,
        on_delete=models.CASCADE,
    )
    supplied_percentage = models.IntegerField(editable=False)
    notes = models.TextField(blank=True)
    credit = models.OneToOneField(
        Balance, related_name="correction", editable=False, on_delete=models.CASCADE
    )
    charge_supplier = models.BooleanField(
        default=True, verbose_name="Charge expenses to supplier"
    )

    def __str__(self):
        return "Correctie van %s%%: %s" % (
            100 - self.supplied_percentage,
            self.order_product,
        )

    def calculate_refund(self):
        """
        Return member refund for this correction.
        This is the amount which the member should be compensated for.
        """
        return Decimal(
            (self.order_product.total_retail_price / Decimal("100.0"))
            * (100 - self.supplied_percentage)
        ).quantize(Decimal(".01"), rounding=ROUND_DOWN)

    def calculate_supplier_refund(self):
        """
        Return supplier refund for this correction.
        This is the amount owed by the supplier for this OrderProduct.

        FIXME: Rename this method to change refund to debit or something?
        """
        if self.charge_supplier is False:
            return Decimal("0")
        return Decimal(
            (self.order_product.total_cost_price() / Decimal("100"))
            * (Decimal("100") - self.supplied_percentage)
        ).quantize(Decimal(".01"), rounding=ROUND_DOWN)

    def _create_credit(self):
        if self.order_product.product.order_round is None:
            order_round = get_current_order_round()
        else:
            order_round = self.order_product.product.order_round

        return Balance.objects.create(
            user=self.order_product.order.user,
            type="CR",
            amount=self.calculate_refund(),
            notes="Correctie in ronde %d, %dx %s, geleverd: %s%%"
            % (
                order_round.id,
                self.order_product.amount,
                self.order_product.product.name,
                self.supplied_percentage,
            ),
        )

    def save(self, **kwargs):
        if self.pk is None:
            self.credit = self._create_credit()
        super(OrderProductCorrection, self).save(**kwargs)

    def delete(self, *args, **kwargs):
        # OneToOne relation isn't cascaded in this direction :(
        # Make sure credit is deleted anyway when correction is deleted
        self.credit.delete()
        super(OrderProductCorrection, self).delete(*args, **kwargs)


class ProductCategory(TimeStampedModel):
    class Meta:
        verbose_name = "Productcategorie"
        verbose_name_plural = "Productcategorieën"

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class ProductUnit(TimeStampedModel):
    class Meta:
        verbose_name = "Producteenheid"
        verbose_name_plural = "Producteenheden"

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=255)
    abbreviations = models.CharField(
        max_length=255, blank=True, help_text="whitespace separated"
    )

    def __str__(self):
        return self.description


class ProductStock(TimeStampedModel):
    """Product purchase / stock"""

    TYPE_ADDED = "added"
    TYPE_LOST = "lost"

    id = models.AutoField(primary_key=True)
    product = models.ForeignKey(
        "Product", related_name="stock", on_delete=models.CASCADE
    )
    amount = models.IntegerField()

    type = models.CharField(
        max_length=8,
        choices=((TYPE_ADDED, "Added"), (TYPE_LOST, "Lost")),
        default=TYPE_ADDED,
        db_index=True,
    )

    notes = models.CharField(max_length=255, null=True, blank=True)

    class Meta:
        verbose_name = verbose_name_plural = "Productvoorraad"

    def __str__(self):
        return "%d x %s" % (self.amount, self.product)

    def save(self, **kwargs):
        if self.pk is not None:
            orig = ProductStock.objects.get(pk=self.pk)
            assert orig.amount == self.amount, "Amount may not be changed!"
            assert orig.product == self.product, "Product may not be changed!"
            assert orig.type == self.type, "Type may not be changed!"

        super(ProductStock, self).save(**kwargs)


class Product(TimeStampedModel):
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Producten"

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    unit = models.ForeignKey(ProductUnit, null=True, on_delete=models.CASCADE)
    unit_amount = models.IntegerField(default=1, help_text='e.g. if half a kilo: "500"')
    base_price = models.DecimalField(max_digits=6, decimal_places=2)
    supplier = models.ForeignKey(
        "Supplier", related_name="products", on_delete=models.CASCADE
    )
    # order_round NULL means: recurring / stock product
    order_round = models.ForeignKey(
        "OrderRound",
        related_name="products",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    # No category means "Other"
    category = models.ForeignKey(
        "ProductCategory",
        related_name="products",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
    )
    new = models.BooleanField(default=False, verbose_name="Show 'new' label")
    maximum_total_order = models.IntegerField(null=True, blank=True)
    enabled = models.BooleanField(default=True)

    # TODO: Prevent deleting of product when it has (paid) orders

    def __str__(self):
        if self.is_stock_product():
            return "[voorraadproduct] %s (%s)" % (self.name, self.supplier)
        if self.order_round:
            return "[ronde %s] %s (%s)" % (
                self.order_round.pk,
                self.name,
                self.supplier,
            )
        return "%s (%s)" % (self.name, self.supplier)

    @property
    def unit_of_measurement(self):
        """
        This function used to be a field,
        it merely exists for backwards compatibility.
        TODO: Check usages, fix them, remove this function.
        """
        return "%s %s" % (self.unit_amount, self.unit.description.lower())

    @property
    def profit(self):
        # TODO move to OrderProduct, update admin views
        return self.retail_price - self.base_price

    @property
    def retail_price(self):
        """
        Return base price plus round's markup percentage,
        rounded up to 2 decimals.
        """
        if self.order_round:
            markup = self.order_round.markup_percentage
        else:
            markup = get_current_order_round().markup_percentage

        total_percentage = 100 + markup
        new_price = (Decimal(self.base_price) / Decimal("100.0")) * Decimal(
            total_percentage
        )
        rounded = new_price.quantize(Decimal(".01"), rounding=ROUND_UP)
        return rounded

    def all_stock(self):
        """
        Total stock bought and lost, can be used to calculate current stock by
        subtracting total orders.
        """
        stock_added = self.stock.filter(type=ProductStock.TYPE_ADDED)
        stock_lost = self.stock.filter(type=ProductStock.TYPE_LOST)
        total_added = sum([s.amount for s in stock_added])
        total_lost = sum([s.amount for s in stock_lost])

        return total_added - total_lost

    @property
    def amount_available(self):
        """
        Return how many items of this product are available.
        Returns None when there is no maximum.
        """
        if self.is_stock_product():
            return self.all_stock() - self.amount_ordered

        if self.maximum_total_order is None:
            return

        maximum = self.maximum_total_order
        total = self.amount_ordered
        return maximum - total

    def verbose_availability(self):
        """
        The value to show in the progress bar in product overview
        """
        if self.is_stock_product():
            available = self.amount_available

            if available == 0:
                return "uitverkocht"

            return "%s in voorraad" % available

        if self.maximum_total_order:
            return "%s van %s" % (self.amount_available, self.maximum_total_order)

        return "Onbeperkt"

    @property
    def amount_ordered(self):
        """
        Return how many items of this product are ordered
        """
        orderproducts = self.orderproducts.filter(order__paid=True)
        total = sum(op.amount for op in orderproducts)
        return total

    @property
    def percentage_available(self):
        """
        Return the percentage of availability of this product.
        Useful for filling progress bars.
        """
        if self.is_stock_product():
            return 100

        if self.maximum_total_order is None:
            return 100
        return int(
            (float(self.amount_available) / float(self.maximum_total_order)) * 100
        )

    @property
    def is_available(self):
        """
        Return if this product is still available for ordering.
        Boolean.
        """
        if self.is_stock_product():
            return self.amount_available > 0

        if self.maximum_total_order is None:
            return True

        return self.amount_available > 0

    def create_corrections(self):
        """
        Create a 0% delivered-correction for all OrderProducts of this product.

        Can be used to automatically create OrderProductCorrections
        when the product was ordered, but not supplied at all.
        """
        for order_product in self.orderproducts.filter(
            correction__isnull=True, order__paid=True
        ):
            OrderProductCorrection.objects.create(
                order_product=order_product,
                supplied_percentage=0,
                notes='Product niet geleverd: "%s" (%s) [%s]'
                % (self.name, self.supplier.name, self.id),
                charge_supplier=True,
            )

    def determine_if_product_is_new_and_set_label(self):
        """
        Set new=True on product when similar product cannot be found in
        previous order round.
        'new' attribute is used to show 'New' label in product list.
        """
        try:
            prev_round = OrderRound.objects.get(id=self.order_round.id - 1)
        except OrderRound.DoesNotExist:
            return

        if not prev_round.products.filter(
            name=self.name, supplier=self.supplier, unit=self.unit
        ):
            self.new = True
            self.save()
            log_event(
                event="Setting product %s to 'new' because I could not find a "
                "similar product in order round %d" % (self, prev_round.id)
            )

    def is_stock_product(self):
        return self.order_round is None


class DraftProduct(TimeStampedModel):
    """
    Product Draft, used to create new products in the backend
    """

    id = models.AutoField(primary_key=True)
    data = JSONField()
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE)
    order_round = models.ForeignKey(OrderRound, on_delete=models.CASCADE)
    is_valid = models.BooleanField(default=False)
    validation_error = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return "[%d] Draft Product [%s]" % (self.id, self.data)

    def validate(self):
        self.is_valid = False
        if not self._valid_name(self.data["name"]):
            self.validation_error = "Naam onjuist"
        elif not self._valid_price(self.data["base_price"]):
            self.validation_error = "Prijs onjuist"
        elif not self._valid_unit(self.data["unit"]):
            self.validation_error = "Eenheid onjuist"
        elif not self._valid_max(self.data["maximum_total_order"]):
            self.validation_error = "Max. onjuist"
        else:
            self.is_valid = True
            self.validation_error = None
        self.save()

    @staticmethod
    def _valid_name(name):
        try:
            return len(name) > 0
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _valid_price(price):
        try:
            float(price)
            return True
        except (ValueError, TypeError):
            return False

    @staticmethod
    def _valid_unit(unit):
        try:
            find_unit(unit)
            return True
        except (RuntimeError, TypeError):
            return False

    @staticmethod
    def _valid_max(max):
        try:
            return max is None or (int(max) and int(max) > 0)
        except ValueError:
            return False

    def create_product(self):
        if not self.is_valid:
            return

        # Decide on unit & amount
        unit = self.data["unit"]
        unit_amount, unit = find_unit(unit)

        prod = Product.objects.create(
            name=self.data["name"],
            description=(self.data["description"] if self.data["description"] else ""),
            unit=unit,
            unit_amount=unit_amount,
            base_price=self.data["base_price"],
            maximum_total_order=self.data["maximum_total_order"],
            supplier=self.supplier,
            order_round=self.order_round,
        )

        if self.data["category"]:
            try:
                prod.category = ProductCategory.objects.get(name=self.data["category"])
                prod.save()
            except ProductCategory.DoesNotExist:
                pass

        return prod

    @property
    def product_data(self):
        return self.data["product_data"]
