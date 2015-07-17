from django.conf import settings
from django.core.urlresolvers import reverse
from mock import MagicMock
from accounts.tests.factories import VokoUserFactory
from finance.tests.factories import BalanceFactory
from ordering.models import Order
from ordering.tests.factories import OrderRoundFactory, OrderProductFactory
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

    def test_given_no_debit_and_unfinished_order_the_order_is_finished_and_we_are_redirected_to_summary_page(self):
        BalanceFactory.create(user=self.user,
                              type="CR",
                              amount=100)

        order = self.user.orders.get_current_order()
        o_p = OrderProductFactory.create(amount=1, product__base_price=10,
                                         order=order, product__order_round=order.order_round)

        assert order.paid is False
        assert o_p.order.total_price < 100
        ret = self.client.get(self.url)

        # Re-fetch
        order = Order.objects.get(pk=order.pk)
        self.assertTrue(order.paid)

        self.assertEqual(ret.status_code, 302)
        self.assertEqual(ret.url, "http://testserver" + reverse('order_summary', args=(order.pk,)))
