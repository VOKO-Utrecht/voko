from datetime import timedelta, datetime
from django.conf import settings
from django.core.urlresolvers import reverse
from mock import MagicMock
from pytz import UTC
from accounts.tests.factories import VokoUserFactory
from finance.models import Payment, Balance
from finance.tests.factories import PaymentFactory
from ordering.models import Order
from ordering.tests.factories import OrderRoundFactory, OrderProductFactory, OrderFactory
from vokou.testing import VokoTestCase


class TestChooseBank(VokoTestCase):
    def setUp(self):
        self.url = reverse('finance.choosebank')
        self.login()

        self.mock_qantani_api = self.patch("finance.views.QantaniAPI")
        self.mock_qantani_api.return_value.get_ideal_banks = MagicMock()

        order_round = OrderRoundFactory.create()
        o_p = OrderProductFactory.create(order__order_round=order_round,
                                         product__order_round=order_round,
                                         order__user=self.user,
                                         order__finalized=True)
        o_p.order.create_debit()
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
        self.assertEqual(payment.balance, None)

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
            self.client.post(self.url, {'bank': 1})

    def test_error_when_order_not_finalized(self):
        self.order.finalized = False
        self.order.save()

        with self.assertRaises(AssertionError):
            self.client.post(self.url, {'bank': 1})

    def test_redirect_on_invalid_form(self):
        ret = self.client.post(self.url, {'bank': 'foo'})
        self.assertRedirects(ret, reverse('finance.choosebank'))

    def test_redirect_when_order_round_is_closed(self):
        month_ago = datetime.now(tz=UTC) - timedelta(days=30)
        order_round = OrderRoundFactory(closed_for_orders=month_ago)
        assert order_round.is_open is False
        self.order.order_round = order_round
        self.order.save()

        ret = self.client.post(self.url, {'bank': 1})
        self.assertRedirects(ret, reverse('finish_order', args=(self.order.id, )), fetch_redirect_response=False)


class TestConfirmTransaction(VokoTestCase):
    def setUp(self):
        self.url = reverse('finance.confirmtransaction')

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

        self.payment = PaymentFactory(order=self.order)

        self.mock_qantani_api = self.patch("finance.views.QantaniAPI")
        self.mock_qantani_api.return_value.get_ideal_banks = MagicMock()
        self.mock_qantani_api.return_value.validate_transaction_checksum = MagicMock()
        self.mock_qantani_api.return_value.validate_transaction_checksum.return_value = True

        self.mock_create_credit = self.patch("finance.models.Payment.create_and_link_credit")
        self.mock_mail_confirmation = self.patch("ordering.models.Order.mail_confirmation")

    def test_required_get_parameters(self):
        ret = self.client.get(self.url, {
            'id': 1234,
            'status': '1',
            'salt': 'pepper',
            'checksum': 'yes',
        })
        self.assertEqual(ret.status_code, 404)

    def test_no_validation_when_status_is_not_1(self):
        ret = self.client.get(self.url, {
            'id': self.payment.transaction_id,
            'status': 'not 1',
            'salt': 'pepper',
            'checksum': 'yes',
        })
        self.assertEqual(ret.status_code, 200)
        self.assertFalse(self.mock_qantani_api.return_value.validate_transaction_checksum.called)

    def test_payment_and_order_status_after_failure_payment(self):
        self.client.get(self.url, {
            'id': self.payment.transaction_id,
            'status': 'not 1',
            'salt': 'pepper',
            'checksum': 'yes',
        })

        payment = Payment.objects.get()
        self.assertFalse(payment.succeeded)
        self.assertFalse(payment.order.paid)
        self.assertFalse(Balance.objects.all())

    def test_that_payment_is_validated(self):
        ret = self.client.get(self.url, {
            'id': self.payment.transaction_id,
            'status': '1',
            'salt': 'pepper',
            'checksum': 'checksum',
        })
        self.assertEqual(ret.status_code, 200)
        self.mock_qantani_api.return_value.validate_transaction_checksum.assert_called_once_with(
            "checksum",
            str(self.payment.transaction_id),
            self.payment.transaction_code,
            "1",
            "pepper"
        )

    def test_payment_and_order_status_after_successful_payment(self):
        self.client.get(self.url, {
            'id': self.payment.transaction_id,
            'status': '1',
            'salt': 'pepper',
            'checksum': 'yes',
        })

        payment = Payment.objects.get()
        self.assertTrue(payment.succeeded)
        self.assertTrue(payment.order.paid)
        self.mock_create_credit.assert_called_once_with()

        debit = Balance.objects.get()
        self.assertEqual(debit.user, payment.order.user)
        self.assertEqual(debit.type, 'DR')
        self.assertEqual(debit.amount, payment.order.total_price)
        self.assertEqual(debit.notes, 'Debit van %s voor bestelling #%s' % (payment.order.total_price,
                                                                            payment.order.id))
        self.mock_mail_confirmation.assert_called_once_with()

    def test_that_order_id_is_removed_from_session_on_successful_payment(self):
        self.client.get(self.url, {
            'id': self.payment.transaction_id,
            'status': '1',
            'salt': 'pepper',
            'checksum': 'yes',
        })

        s = self.client.session
        self.assertNotIn('order_to_pay', s)

    def test_payment_status_in_context(self):
        ret = self.client.get(self.url, {
            'id': self.payment.transaction_id,
            'status': '1',
            'salt': 'pepper',
            'checksum': 'yes',
        })
        self.assertEqual(ret.context[0]['payment_succeeded'], True)


class TestQantaniCallbackView(VokoTestCase):
    def setUp(self):
        self.url = reverse('finance.callback')

        self.user = VokoUserFactory.create()
        self.user.set_password('secret')
        self.user.is_active = True
        self.user.save()
        self.client.login(username=self.user.email, password='secret')

        self.order = OrderFactory(user=self.user,
                                  finalized=True,
                                  paid=False)
        self.payment = PaymentFactory(order=self.order)

        s = self.client.session
        s['order_to_pay'] = self.order.id
        s.save()

        self.mock_qantani_api = self.patch("finance.views.QantaniAPI")
        self.mock_qantani_api.return_value.validate_transaction_checksum = MagicMock()
        self.mock_qantani_api.return_value.validate_transaction_checksum.return_value = True

        self.mock_complete_after_payment = self.patch("ordering.models.Order.complete_after_payment")
        self.mock_create_credit = self.patch("finance.models.Payment.create_and_link_credit")
        self.mock_mail_failure_notification = self.patch("ordering.models.Order.mail_failure_notification")

    def test_404_when_payment_cannot_be_found(self):
        ret = self.client.get(self.url, {
            'id': 666,
            'status': 'not 1',
            'salt': 'pepper',
            'checksum': 'yes',
        })

        self.assertEqual(ret.status_code, 404)

    def test_empty_response_on_validation_failure(self):
        self.mock_qantani_api.return_value.validate_transaction_checksum.return_value = False
        ret = self.client.get(self.url, {
            'id': self.payment.transaction_id,
            'status': '1',
            'salt': 'pepper',
            'checksum': 'yes',
        })

        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.content, "")

    def test_payment_is_set_to_succeeded_when_payment_is_valid(self):
        assert self.payment.succeeded is False
        self.client.get(self.url, {
            'id': self.payment.transaction_id,
            'status': '1',
            'salt': 'pepper',
            'checksum': 'yes',
        })

        payment = Payment.objects.get()
        self.assertTrue(payment.succeeded)

    def test_response_on_valid_payment(self):
        ret = self.client.get(self.url, {
            'id': self.payment.transaction_id,
            'status': '1',
            'salt': 'pepper',
            'checksum': 'yes',
        })

        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.content, "+")

    def test_order_is_completed_when_order_paid_is_false(self):
        assert self.order.paid is False
        self.client.get(self.url, {
            'id': self.payment.transaction_id,
            'status': '1',
            'salt': 'pepper',
            'checksum': 'yes',
        })

        payment = Payment.objects.get()
        self.mock_create_credit.assert_called_once_with()
        self.mock_complete_after_payment.assert_called_once_with()

    def test_order_is_not_completed_when_round_is_closed_and_notification_is_sent(self):
        month_ago = datetime.now(tz=UTC) - timedelta(days=30)
        order_round = OrderRoundFactory(closed_for_orders=month_ago)
        assert order_round.is_open is False
        self.order.order_round = order_round
        self.order.save()

        assert self.order.paid is False
        self.client.get(self.url, {
            'id': self.payment.transaction_id,
            'status': '1',
            'salt': 'pepper',
            'checksum': 'yes',
        })

        payment = Payment.objects.get()
        self.assertFalse(payment.order.paid)
        self.mock_create_credit.assert_called_once_with()
        self.assertFalse(self.mock_complete_after_payment.called)

        self.mock_mail_failure_notification.assert_called_once_with()


class TestCancelPaymentView(VokoTestCase):
    def setUp(self):
        self.url = reverse('finance.cancelpayment')

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

    def test_order_finalized_is_set_to_false(self):
        self.client.get(self.url)
        order = Order.objects.get()
        self.assertFalse(order.finalized)

    def test_redirect_to_finish_order(self):
        ret = self.client.get(self.url)
        self.assertRedirects(ret, "http://testserver%s" %
                             reverse('finish_order', args=(self.order.id,)),
                             fetch_redirect_response=False)