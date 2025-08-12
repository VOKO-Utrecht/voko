from factory import Sequence, LazyAttribute
from factory.django import DjangoModelFactory
from factory.fuzzy import FuzzyText


class VokoUserFactory(DjangoModelFactory):
    class Meta:
        model = "accounts.VokoUser"

    first_name = Sequence(lambda n: "John%s" % n)
    last_name = Sequence(lambda n: "Doe%s" % n)
    email = LazyAttribute(lambda o: "%s@example.org" % o.last_name)
    is_active = True


class AddressFactory(DjangoModelFactory):
    class Meta:
        model = "accounts.Address"

    zip_code = FuzzyText(length=6)
