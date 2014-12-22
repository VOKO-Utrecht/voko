import factory


class BalanceFactory(factory.DjangoModelFactory):
    class Meta:
        model = "finance.Balance"

