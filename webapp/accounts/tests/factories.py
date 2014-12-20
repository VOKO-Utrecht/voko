import factory
from factory.fuzzy import FuzzyText


class VokoUserFactory(factory.DjangoModelFactory):
    class Meta:
        model = "accounts.VokoUser"

    first_name = factory.Sequence(lambda n: 'John%s' % n)
    last_name = factory.Sequence(lambda n: 'Doe%s' % n)
    email = factory.LazyAttribute(lambda o: '%s@example.org' % o.last_name)
    is_active = True


class AddressFactory(factory.DjangoModelFactory):
    class Meta:
        model = "accounts.Address"

    zip_code = FuzzyText(length=6)