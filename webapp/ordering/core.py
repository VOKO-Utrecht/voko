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
    filtered = order_rounds.filter(open_for_orders__lte=now,
                                   collect_datetime__gt=now)
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
    return order_rounds.filter(
        collect_datetime__lt=now
    ).order_by("collect_datetime").reverse().first()


def get_next_order_round():
    """
    Return the order round after the current round.

    :return: OrderRound object || None
    """
    order_rounds = models.OrderRound.objects.all()
    return order_rounds.filter(
        open_for_orders__gt=get_current_order_round().open_for_orders
    ).order_by("open_for_orders").first()


def get_or_create_order(user):
    current_order_round = get_current_order_round()

    if current_order_round is None:
        raise RuntimeError("Nog geen bestelronde aangemaakt!")

    order = models.Order.objects.filter(
        paid=False,
        user=user,
        order_round=get_current_order_round()
    ).order_by('id').last()

    if order is None:
        order = models.Order.objects.create(
            paid=False,
            user=user,
            order_round=get_current_order_round()
        )
    return order


def get_order_product(product, order):
    existing_ops = models.OrderProduct.objects.filter(product=product,
                                                      order=order)
    if existing_ops:
        return existing_ops[0]


def update_totals_for_products_with_max_order_amounts(order, request=None):
    """
    request (Django request) is optional, when given it is used to add
    a message when orderproducts are altered or removed.
    """

    # stock products
    stock_products = order.orderproducts.all().filter(
        product__order_round__exact=None)
    capped_products = order.orderproducts.all().exclude(
        product__maximum_total_order__exact=None)

    for orderproduct in stock_products | capped_products:
        if orderproduct.amount > orderproduct.product.amount_available:
            if orderproduct.product.amount_available > 0:
                orderproduct.amount = orderproduct.product.amount_available
                orderproduct.save()

                if request:
                    messages.add_message(
                        request, messages.WARNING,
                        "Je bestelling van product %s is verlaagd naar "
                        "%d in verband met beschikbaarheid." %
                        (orderproduct.product.name,
                         orderproduct.product.amount_available))

            else:
                orderproduct.delete()
                if request:
                    messages.add_message(
                        request, messages.WARNING,
                        "Je bestelling van product %s is verwijderd "
                        "omdat het product inmiddels is uitverkocht." %
                        (orderproduct.product.name,))


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

    if amount == '':
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
