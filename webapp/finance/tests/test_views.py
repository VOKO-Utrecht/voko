from unittest import skip
from django.conf import settings
from django.core.urlresolvers import reverse
from mock import MagicMock
from accounts.tests.factories import VokoUserFactory
from finance.models import Payment
from ordering.tests.factories import OrderRoundFactory, OrderProductFactory, OrderFactory
from vokou.testing import VokoTestCase


class TestChooseBank(VokoTestCase):
    def setUp(self):
        self.url = reverse('finance.choosebank')

        self.user = VokoUserFactory.create()
        self.user.set_password('secret')
        self.user.is_active = True
        self.user.save()
        self.client.login(username=self.user.email, password='secret')

        self.mock_qantani_api = self.patch("finance.views.QantaniAPI")
        self.mock_qantani_api.return_value.get_ideal_banks = MagicMock()

        order_round = OrderRoundFactory.create()
        o_p = OrderProductFactory.create(order__order_round=order_round,
                                         product__order_round=order_round,
                                         order__user=self.user)
        o_p.order.create_and_link_debit()
        o_p.save()
        self.order = o_p.order

        s = self.client.session
        s['order_to_pay'] = self.order.id
        s.save()

    def test_that_qantani_api_client_is_initiated(self):
        self.client.get(self.url)
        self.mock_qantani_api.assert_called_once_with(settings.QANTANI_MERCHANT_ID,
                                                      settings.QANTANI_MERCHANT_KEY,
                                                      settings.QANTANI_MERCHANT_SECRET)

    def test_that_list_of_banks_is_requested(self):
        self.client.get(self.url)
        self.mock_qantani_api.return_value.get_ideal_banks.assert_called_once_with()

    def test_that_context_contains_form_with_bank_choices(self):
        banks = [
            {'Id': 'EXAMPLE_BANK', 'Name': "Example Bank"},
            {'Id': 'ANOTHER_BANK', 'Name': "Another Bank"}
        ]
        self.mock_qantani_api.return_value.get_ideal_banks.return_value = banks

        ret = self.client.get(self.url)
        form = ret.context[1].get('form')
        expected = [tuple(x.values()) for x in banks]
        self.assertEqual(form.fields.get('bank').choices, expected)

    def test_order_is_placed_in_context(self):
        ret = self.client.get(self.url)
        self.assertEqual(ret.context[0]['order'], self.order)


class TestCreateTransaction(VokoTestCase):
    def setUp(self):
        self.url = reverse('finance.createtransaction')

        self.user = VokoUserFactory.create()
        self.user.set_password('secret')
        self.user.is_active = True
        self.user.save()
        self.client.login(username=self.user.email, password='secret')

        self.order = OrderFactory(user=self.user,
                                  finalized=True,
                                  paid=False)

        s = self.client.session
        s['order_to_pay'] = self.order.id
        s.save()

        self.mock_qantani_api = self.patch("finance.views.QantaniAPI")
        self.mock_qantani_api.return_value.get_ideal_banks = MagicMock()
        self.mock_qantani_api.return_value.create_ideal_transaction = MagicMock()
        self.mock_qantani_api.return_value.get_ideal_banks.return_value = [{'Id': 1, 'Name': 'TestBank'}]

    def test_that_transaction_is_created(self):
        self.client.post(self.url, {'bank': 1})
        self.mock_qantani_api.return_value.create_ideal_transaction.assert_called_once_with(
            amount=self.order.total_price_to_pay_with_balances_taken_into_account(),
            description="VOKO Utrecht ID %d" % self.order.id,
            return_url="http://leden.vokoutrecht.nl/finance/pay/transaction/confirm/",
            bank_id='1'
        )

    def test_that_payment_object_is_created(self):
        assert Payment.objects.count() == 0

        self.mock_qantani_api.return_value.create_ideal_transaction.return_value = {
            "TransactionID": 1212,
            "Code": "code",
            "BankURL": "http://bank.url"
        }

        self.client.post(self.url, {'bank': 1})
        payment = Payment.objects.get()
        self.assertEqual(payment.amount, self.order.total_price_to_pay_with_balances_taken_into_account())
        self.assertEqual(payment.order, self.order)
        self.assertEqual(payment.transaction_id, 1212)
        self.assertEqual(payment.transaction_code, "code")

    def test_that_user_is_redirected_to_bank_url(self):
        self.mock_qantani_api.return_value.create_ideal_transaction.return_value = {
            "TransactionID": 1212,
            "Code": "code",
            "BankURL": "http://bank.url"
        }

        ret = self.client.post(self.url, {'bank': 1})
        self.assertEqual(ret.status_code, 302)
        self.assertEqual(ret.url, "http://bank.url")

    def test_error_when_user_doesnt_own_order(self):
        s = self.client.session
        s['order_to_pay'] = OrderFactory().id
        s.save()

        with self.assertRaises(AssertionError):
            self.client.post(self.url)

    def test_error_when_order_not_finalized(self):
        self.order.finalized = False
        self.order.save()

        with self.assertRaises(AssertionError):
            self.client.post(self.url, {'bank': 1})

    @skip("Cannot seem to get the form invalid")
    def test_redirect_on_invalid_form(self):
        ret = self.client.post(self.url, {'bank': 'foo'})
        self.assertEqual(ret.status_code, 200)

