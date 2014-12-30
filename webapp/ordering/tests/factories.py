import datetime
from factory import DjangoModelFactory, SubFactory, LazyAttribute
from factory.fuzzy import FuzzyDateTime, FuzzyText, FuzzyChoice, FuzzyDecimal, FuzzyInteger
from pytz import UTC
from accounts.tests.factories import AddressFactory, VokoUserFactory
from ordering.models import Product


class OrderRoundFactory(DjangoModelFactory):
    class Meta:
        model = "ordering.OrderRound"

    open_for_orders = datetime.datetime.now(tz=UTC)
    closed_for_orders = open_for_orders + datetime.timedelta(days=4)
    collect_datetime = closed_for_orders + datetime.timedelta(days=5)

    transaction_costs = FuzzyDecimal(low=0, high=0.40)
    markup_percentage = FuzzyDecimal(low=0, high=10)


class SupplierFactory(DjangoModelFactory):
    class Meta:
        model = "ordering.Supplier"

    name = FuzzyText()
    address = SubFactory(AddressFactory)
    email = LazyAttribute(lambda o: '%s@example.org' % o.name)


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = "ordering.Product"

    name = FuzzyText()
    description = FuzzyText()
    unit_of_measurement = FuzzyChoice(Product.UNITS)
    base_price = FuzzyDecimal(0.1, 6.0)
    supplier = SubFactory(SupplierFactory)
    order_round = SubFactory(OrderRoundFactory)


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = "ordering.Order"

    order_round = SubFactory(OrderRoundFactory)
    user = SubFactory(VokoUserFactory)


class OrderProductFactory(DjangoModelFactory):
    class Meta:
        model = "ordering.OrderProduct"

    product = SubFactory(ProductFactory)
    order = SubFactory(OrderFactory)
    amount = FuzzyInteger(low=1, high=10)