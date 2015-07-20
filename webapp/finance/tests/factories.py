from factory.fuzzy import FuzzyInteger, FuzzyText, FuzzyDecimal
from ordering.tests.factories import OrderFactory
from factory import DjangoModelFactory, SubFactory


class BalanceFactory(DjangoModelFactory):
    class Meta:
        model = "finance.Balance"


class PaymentFactory(DjangoModelFactory):
    class Meta:
        model = "finance.Payment"

    order = SubFactory(OrderFactory)
    amount = FuzzyDecimal(low=1, high=99)

    transaction_id = FuzzyInteger(low=1, high=999)
    transaction_code = FuzzyText()

