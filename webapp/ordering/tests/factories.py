import datetime
from factory import DjangoModelFactory, SubFactory, LazyAttribute, SelfAttribute
from factory.fuzzy import FuzzyText, FuzzyDecimal, FuzzyInteger
from pytz import UTC
from accounts.tests.factories import AddressFactory, VokoUserFactory


class OrderRoundFactory(DjangoModelFactory):
    """
    Creates an OPEN order round
    """
    class Meta:
        model = "ordering.OrderRound"

    open_for_orders = datetime.datetime.now(tz=UTC)
    closed_for_orders = open_for_orders + datetime.timedelta(days=4)
    collect_datetime = closed_for_orders + datetime.timedelta(days=5)

    transaction_costs = FuzzyDecimal(low=0.01, high=0.40)
    markup_percentage = FuzzyDecimal(low=1, high=10)


class SupplierFactory(DjangoModelFactory):
    class Meta:
        model = "ordering.Supplier"

    name = FuzzyText()
    address = SubFactory(AddressFactory)
    email = LazyAttribute(lambda o: '%s@example.org' % o.name)


class ProductUnitFactory(DjangoModelFactory):
    class Meta:
        model = "ordering.ProductUnit"

    name = FuzzyText()
    description = FuzzyText()
    abbreviations = ""


class ProductFactory(DjangoModelFactory):
    class Meta:
        model = "ordering.Product"

    name = FuzzyText()
    description = FuzzyText()
    unit_amount = FuzzyInteger(low=1, high=100)
    unit = SubFactory(ProductUnitFactory)
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
    retail_price = SelfAttribute('product.retail_price')
    base_price = SelfAttribute('product.base_price')


class OrderProductCorrectionFactory(DjangoModelFactory):
    class Meta:
        model = "ordering.OrderProductCorrection"

    order_product = SubFactory("ordering.tests.factories.OrderProductFactory", order__paid=True, order__finalized=True)
    supplied_percentage = FuzzyInteger(low=0, high=90)
    notes = FuzzyText()
    # credit = SubFactory("finance.tests.factories.BalanceFactory")  # TODO: amount should not be random
    # Credit is created by save() function on model
    # charge_supplier = FuzzyChoice(True, False)


class UnitFactory(DjangoModelFactory):
    class Meta:
            model = "ordering.ProductUnit"

    name = FuzzyText()
    description = FuzzyText()


class ProductCategoryFactory(DjangoModelFactory):
    class Meta:
            model = "ordering.ProductCategory"

    name = FuzzyText()

