from factory.django import DjangoModelFactory
from factory import SubFactory
from accounts.tests.factories import VokoUserFactory
from ordering.tests.factories import OrderRoundFactory


class RideFactory(DjangoModelFactory):
    """
    Creates a ride
    """
    class Meta:
        model = "transport.Ride"

    order_round = SubFactory(OrderRoundFactory)
    driver = SubFactory(VokoUserFactory)
    codriver = SubFactory(VokoUserFactory)
