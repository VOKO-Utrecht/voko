from django.contrib import messages
from pytz import UTC
import re
from datetime import datetime
from ordering import models


def get_current_order_round():
    """
    Return the current order round.
    If there's no current order round, return the next one.
    If there's not current or next order round, return the previous one.
    If there's no order round at all, return None.

    :return: OrderRound object || None
    """
    now = datetime.now(UTC)
    order_rounds = models.OrderRound.objects.all()

    # Exact match to open round(s)
    filtered = order_rounds.filter(open_for_orders__lte=now, collect_datetime__gt=now)
    if filtered:
        return filtered.first()  # First, if there are multiple open rounds

    # Future round(s)
    filtered = order_rounds.filter(open_for_orders__gte=now)
    if filtered.count() > 0:
        return filtered.order_by("open_for_orders")[0]

    # Previous round(s)
    filtered = order_rounds.filter(collect_datetime__lt=now)
    if filtered.count() > 0:
        return filtered.order_by("-open_for_orders")[0]


def get_last_order_round():
    """
    Return the most recent finished order round, after collecting time

    :return: OrderRound object || None
    """
    now = datetime.now(UTC)
    order_rounds = models.OrderRound.objects.all()
    return order_rounds.filter(collect_datetime__lt=now).order_by("collect_datetime").reverse().first()


def get_next_order_round():
    """
    Return the order round after the current round.

    :return: OrderRound object || None
    """
    order_rounds = models.OrderRound.objects.all()
    return (
        order_rounds.filter(open_for_orders__gt=get_current_order_round().open_for_orders)
        .order_by("open_for_orders")
        .first()
    )


def get_or_create_order(user):
    current_order_round = get_current_order_round()

    if current_order_round is None:
        raise RuntimeError("Nog geen bestelronde aangemaakt!")

    order = (
        models.Order.objects.filter(paid=False, user=user, order_round=get_current_order_round()).order_by("id").last()
    )

    if order is None:
        order = models.Order.objects.create(paid=False, user=user, order_round=get_current_order_round())
    return order


def get_order_product(product, order):
    existing_ops = models.OrderProduct.objects.filter(product=product, order=order)
    if existing_ops:
        return existing_ops[0]


def update_totals_for_products_with_max_order_amounts(order, request=None):
    """
    request (Django request) is optional, when given it is used to add
    a message when orderproducts are altered or removed.
    """

    # stock products
    stock_products = order.orderproducts.all().filter(product__order_round__exact=None)
    capped_products = order.orderproducts.all().exclude(product__maximum_total_order__exact=None)

    for orderproduct in stock_products | capped_products:
        if orderproduct.amount > orderproduct.product.amount_available:
            if orderproduct.product.amount_available > 0:
                orderproduct.amount = orderproduct.product.amount_available
                orderproduct.save()

                if request:
                    messages.add_message(
                        request,
                        messages.WARNING,
                        "Je bestelling van product %s is verlaagd naar "
                        "%d in verband met beschikbaarheid."
                        % (orderproduct.product.name, orderproduct.product.amount_available),
                    )

            else:
                orderproduct.delete()
                if request:
                    messages.add_message(
                        request,
                        messages.WARNING,
                        "Je bestelling van product %s is verwijderd "
                        "omdat het product inmiddels is uitverkocht." % (orderproduct.product.name,),
                    )


def find_unit(unit):
    """
    Find ProductUnit object closest to :unit: string & amount.
    Return tuple of (amount, ProductUnit)
    Raise RuntimeError when not matchable
    """

    unit = str(unit)
    unit = unit.strip() if unit else unit
    # optional amount, optional whitespace, 1+ sentence
    regex = r"^(\d*)\s?([a-zA-Z0-9() ]+)"
    match = re.match(regex, unit)

    if not match:
        raise RuntimeError("No units could be matched")

    amount, unit_str = match.groups()
    unit_str = unit_str.lower().strip()

    if amount == "":
        amount = 1
    else:
        amount = int(amount)

    by_name = _find_unit_by_name(unit_str)
    by_desc = _find_unit_by_desc(unit_str)
    by_abbr = _find_unit_by_abbr(unit_str)

    if by_name:
        return amount, by_name

    if by_desc:
        return amount, by_desc

    if by_abbr:
        return amount, by_abbr

    raise RuntimeError("No units could be matched")


def _find_unit_by_name(unit):
    try:
        return models.ProductUnit.objects.get(name__iexact=unit)
    except models.ProductUnit.DoesNotExist:
        return


def _find_unit_by_desc(unit):
    try:
        return models.ProductUnit.objects.get(description__iexact=unit)
    except models.ProductUnit.DoesNotExist:
        return


def _find_unit_by_abbr(unit):
    for product_unit in models.ProductUnit.objects.all():
        abbrs = [a.lower() for a in product_unit.abbreviations.split()]
        if unit in abbrs:
            return product_unit
        if unit + "." in abbrs:
            return product_unit


def calculate_next_orderround_dates(
    interval_weeks=2, open_hour=10, close_hour=20, duration_hours=72, collect_days_after=4, collect_hour=14
):
    """
    Calculate dates for the next order round based on configuration.

    Args:
        interval_weeks: How many weeks between order rounds
        open_hour: Hour when order rounds open (0-23)
        close_hour: Hour when order rounds close (0-23)
        duration_hours: How long order rounds stay open (hours)
        collect_days_after: Days after closing when products can be collected
        collect_hour: Hour when products can be collected (0-23)

    Returns:
        tuple: (open_datetime, close_datetime, collect_datetime)
    """
    from datetime import datetime, timedelta
    import pytz

    # Get the last order round to calculate from
    last_round = get_last_order_round()

    if last_round:
        # Calculate next round based on the last round's opening date
        base_date = last_round.open_for_orders.date()
        next_open_date = base_date + timedelta(weeks=interval_weeks)
    else:
        # If no previous rounds, start from next Sunday
        today = datetime.now(pytz.UTC).date()
        days_until_sunday = (6 - today.weekday()) % 7
        if days_until_sunday == 0:  # If today is Sunday, use next Sunday
            days_until_sunday = 7
        next_open_date = today + timedelta(days=days_until_sunday)

    # Create datetimes
    open_datetime = datetime.combine(next_open_date, datetime.min.time().replace(hour=open_hour))
    open_datetime = pytz.UTC.localize(open_datetime)

    close_datetime = open_datetime + timedelta(hours=duration_hours)

    collect_date = close_datetime.date() + timedelta(days=collect_days_after)
    collect_datetime = datetime.combine(collect_date, datetime.min.time().replace(hour=collect_hour))
    collect_datetime = pytz.UTC.localize(collect_datetime)

    return open_datetime, close_datetime, collect_datetime


def should_create_new_orderround(create_days_ahead=7):
    """
    Check if we should create a new order round.

    Args:
        create_days_ahead: How many days ahead to create new order rounds

    Returns:
        bool: True if a new order round should be created
    """
    from datetime import datetime, timedelta
    import pytz

    # Check if there's already a future order round
    future_rounds = models.OrderRound.objects.filter(open_for_orders__gt=datetime.now(pytz.UTC)).order_by(
        "open_for_orders"
    )

    if not future_rounds.exists():
        # No future rounds, we should create one
        return True

    # Check if the next future round is far enough ahead
    next_round = future_rounds.first()
    if next_round is None:
        return True

    cutoff_date = datetime.now(pytz.UTC) + timedelta(days=create_days_ahead)

    return next_round.open_for_orders > cutoff_date


def create_orderround_automatically():
    """
    Create a new order round automatically based on configuration.

    Returns:
        OrderRound or None: The created order round, or None if creation failed
    """
    from constance import config
    from log import log_event

    if not config.AUTO_CREATE_ORDERROUNDS:
        return None

    if not should_create_new_orderround(config.ORDERROUND_CREATE_DAYS_AHEAD):
        return None

    try:
        open_datetime, close_datetime, collect_datetime = calculate_next_orderround_dates(
            interval_weeks=config.ORDERROUND_INTERVAL_WEEKS,
            open_hour=config.ORDERROUND_OPEN_HOUR,
            close_hour=config.ORDERROUND_CLOSE_HOUR,
            duration_hours=config.ORDERROUND_DURATION_HOURS,
            collect_days_after=config.ORDERROUND_COLLECT_DAYS_AFTER,
            collect_hour=config.ORDERROUND_COLLECT_HOUR,
        )

        # Get default pickup location and transport coordinator
        default_pickup = None
        transport_coordinator = None

        if hasattr(config, "ORDERROUND_DEFAULT_PICKUP_LOCATION") and config.ORDERROUND_DEFAULT_PICKUP_LOCATION:
            try:
                default_pickup = models.PickupLocation.objects.get(pk=config.ORDERROUND_DEFAULT_PICKUP_LOCATION)
            except models.PickupLocation.DoesNotExist:
                # Fallback to default pickup location
                default_pickup = models.PickupLocation.objects.filter(is_default=True).first()
        else:
            default_pickup = models.PickupLocation.objects.filter(is_default=True).first()

        if (
            hasattr(config, "ORDERROUND_DEFAULT_TRANSPORT_COORDINATOR")
            and config.ORDERROUND_DEFAULT_TRANSPORT_COORDINATOR
        ):
            try:
                from accounts.models import VokoUser

                transport_coordinator = VokoUser.objects.get(pk=config.ORDERROUND_DEFAULT_TRANSPORT_COORDINATOR)
            except Exception:
                pass  # Leave as None if user doesn't exist or import fails

        # Create the new order round
        order_round = models.OrderRound.objects.create(
            open_for_orders=open_datetime,
            closed_for_orders=close_datetime,
            collect_datetime=collect_datetime,
            markup_percentage=config.MARKUP_PERCENTAGE,
            pickup_location=default_pickup,
            transport_coordinator=transport_coordinator,
        )

        log_event(event="Auto-created order round #%d" % order_round.pk)

        return order_round

    except Exception as e:
        log_event(event="Failed to auto-create order round: %s" % str(e))
        return None
