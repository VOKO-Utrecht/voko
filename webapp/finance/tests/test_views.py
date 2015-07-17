from django.conf import settings
from django.core.urlresolvers import reverse
from mock import MagicMock
from accounts.tests.factories import VokoUserFactory
from finance.tests.factories import BalanceFactory
from ordering.models import Order
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
