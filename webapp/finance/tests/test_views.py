from django.conf import settings
from django.core.urlresolvers import reverse
from mock import MagicMock
from accounts.tests.factories import VokoUserFactory
from ordering.tests.factories import OrderRoundFactory
from vokou.testing import VokoTestCase


class TestChooseBank(VokoTestCase):
    def setUp(self):
        self.url = reverse('finance.choosebank')
        user = VokoUserFactory.create()
        user.save()
        user.set_password('secret')
        user.is_active = True
        user.save()
        self.client.login(username=user.email, password='secret')

        self.mock_qantani_api = self.patch("finance.views.QantaniAPI")
        self.mock_qantani_api.return_value.get_ideal_banks = MagicMock()

        OrderRoundFactory.create()

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

