from accounts.models import VokoUser
from finance.models import Balance
from vokou.testing import VokoTestCase


class TestBalanceManager(VokoTestCase):
    def setUp(self):
        self.vokouser = VokoUser.objects.create(email="test@example.com",
                                                first_name="John",
                                                last_name="Doe")

    def tearDown(self):
        self.vokouser.delete()

    def test_methods_on_user_object_via_balance_model(self):
        self.vokouser.balance.credit()
        self.vokouser.balance.debit()

    def test_simple_credit(self):
        Balance.objects.create(user=self.vokouser,
                               type="CR",
                               amount=11.11)
        self.assertEqual(float(self.vokouser.balance.credit()), 11.11)
        self.assertEqual(self.vokouser.balance.debit(), 0)

    def test_simple_debit(self):
        Balance.objects.create(user=self.vokouser,
                               type="DR",
                               amount=22.22)
        self.assertEqual(float(self.vokouser.balance.debit()), 22.22)
        self.assertEqual(self.vokouser.balance.credit(), 0)

    def test_that_debit_and_credit_even_each_other_out(self):
        self.vokouser.balance.create(type="CR", amount=12)
        self.vokouser.balance.create(type="CR", amount=0.99)
        self.vokouser.balance.create(type="DR", amount=12)
        self.vokouser.balance.create(type="DR", amount=0.99)

        self.assertEqual(self.vokouser.balance.credit(), 0)
        self.assertEqual(self.vokouser.balance.debit(), 0)

