import re
from datetime import datetime, timedelta, date

import pytz
from accounts.models import VokoUser
from constance import config
from django.contrib import messages
from log import log_event
from pytz import UTC
from tzlocal import get_localzone

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


def get_latest_order_round():
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


def get_last_order_round():
    """
    Return the last order round that exists.

    :return: OrderRound object || None
    """
    order_rounds = models.OrderRound.objects.all()
    return order_rounds.order_by("open_for_orders").last()


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


def calculate_next_orderround_dates(open_date):
    """
    Calculate dates for the next order round based on configuration.

    Returns:
        tuple: (open_datetime, close_datetime, collect_datetime)
    """
    # Create datetimes
    open_datetime = datetime.combine(open_date, datetime.min.time().replace(hour=config.ORDERROUND_OPEN_HOUR)).replace(
        tzinfo=get_localzone()
    )

    close_datetime = open_datetime + timedelta(hours=config.ORDERROUND_DURATION_HOURS)

    collect_date = close_datetime.date() + timedelta(days=config.ORDERROUND_COLLECT_DAYS_AFTER)
    collect_datetime = datetime.combine(
        collect_date, datetime.min.time().replace(hour=config.ORDERROUND_COLLECT_HOUR)
    ).replace(tzinfo=get_localzone())

    return open_datetime, close_datetime, collect_datetime


def get_quarter_end_dates():
    """
    Get the last day of the current quarter and the last day of the next quarter as date objects.

    Returns:
        tuple: (last_day_current_quarter, last_day_next_quarter)
    """
    now = datetime.now(pytz.UTC)
    current_quarter = (now.month - 1) // 3 + 1
    next_quarter = current_quarter + 1

    # Handle year rollover for next quarter
    year = now.year
    if next_quarter > 4:
        next_quarter = 1
        year += 1

    # Calculate last month of current quarter
    last_month_of_current_quarter = current_quarter * 3

    # Get first day of the month after current quarter
    if last_month_of_current_quarter == 12:
        next_month_first_day = date(now.year + 1, 1, 1)
    else:
        next_month_first_day = date(now.year, last_month_of_current_quarter + 1, 1)

    # Last day of current quarter
    last_day_of_current_quarter = next_month_first_day - timedelta(days=1)

    # Calculate last month of next quarter
    last_month_of_next_quarter = next_quarter * 3

    # Get first day of the month after next quarter
    if last_month_of_next_quarter == 12:
        next_month_first_day = date(year + 1, 1, 1)
    else:
        next_month_first_day = date(year, last_month_of_next_quarter + 1, 1)

    # Last day of next quarter
    last_day_of_next_quarter = next_month_first_day - timedelta(days=1)

    return last_day_of_current_quarter, last_day_of_next_quarter


def create_orderround_batch():
    """
    Create a new order round batch automatically based on configuration.

    Returns:
        list[models.OrderRound]: The order round batches created
    """
    # Get the last day of the current and next quarter
    last_day_current_quarter, last_day_next_quarter = get_quarter_end_dates()

    # Check if we should create a new order round batch
    last_round = get_last_order_round()
    current_date = datetime.now(pytz.UTC).date()

    # Determine start date based on whether there's a last round
    if last_round is None:
        start_date = current_date + timedelta(days=7)
    else:
        start_date = last_round.open_for_orders.date() + timedelta(weeks=config.ORDERROUND_INTERVAL_WEEKS)

    # Determine end date based on proximity to next quarter
    if last_day_current_quarter < current_date + timedelta(days=config.ORDERROUND_CREATE_DAYS_AHEAD):
        # Next quarter is close, create batch for next quarter
        end_date = last_day_next_quarter
    elif last_round is None or start_date <= last_day_current_quarter:
        # Fill current quarter
        end_date = last_day_current_quarter
    else:
        # No new order round batch needed
        return []

    # Adjust start date to the configured open day of the week
    days_until_target = (config.ORDERROUND_OPEN_DAY_OF_WEEK - start_date.weekday()) % 7
    start_date += timedelta(days=days_until_target)
    # Calculate the end date for the next quarter
    # This will be the last day of the next quarter
    order_rounds = []
    while start_date <= end_date:
        if start_date > current_date:
            open_datetime, close_datetime, collect_datetime = calculate_next_orderround_dates(start_date)

            # Get default pickup location and transport coordinator
            pickup_location = models.PickupLocation.objects.filter(is_default=True).first()
            transport_coordinator = VokoUser.objects.filter(pk=config.ORDERROUND_TRANSPORT_COORDINATOR).first()

            order_round = models.OrderRound.objects.create(
                open_for_orders=open_datetime,
                closed_for_orders=close_datetime,
                collect_datetime=collect_datetime,
                markup_percentage=config.MARKUP_PERCENTAGE,
                pickup_location=pickup_location,
                transport_coordinator=transport_coordinator,
            )

            order_rounds.append(order_round)

            log_event(event="Auto-created order round #%d" % order_round.pk)

        start_date += timedelta(weeks=config.ORDERROUND_INTERVAL_WEEKS)

    return order_rounds
