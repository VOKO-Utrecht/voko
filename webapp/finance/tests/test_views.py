from datetime import timedelta, datetime
from django.conf import settings
from django.urls import reverse
from mock import MagicMock
from pytz import UTC
from accounts.tests.factories import VokoUserFactory
from finance.models import Payment, Balance
from finance.tests.factories import PaymentFactory
from ordering.models import Order
from ordering.tests.factories import (OrderRoundFactory, OrderFactory)
from vokou.testing import VokoTestCase, suppressWarnings


class FinanceTestCase(VokoTestCase):
    def setUp(self):
        self.mollie_client = self.patch("finance.views.MollieClient")
        self.mollie_client.return_value.issuers.all.return_value = \
            MagicMock()
        self.mollie_methods = self.patch("finance.views.MollieMethods")
        self.mollie_methods.IDEAL = 'ideal'
        self.mollie_methods.BANCONTACT = 'bancontact'

        # we only support bancontact and iDeal payment methods
        methods = [
            {'id': 'bancontact', 'description': 'Bancontact',
             'status': 'activated'},
            {'id': 'ideal', 'description': 'iDeal', 'status': 'activated',
                'issuers': [{'id': 'EXAMPLE_BANK', 'name': "Example Bank"},
                            {'id': 'ANOTHER_BANK', 'name': "Another Bank"}]}
        ]
        self.mollie_client.return_value.methods.all.return_value = methods

        self.user = VokoUserFactory.create()
        self.user.set_password('secret')
        self.user.is_active = True
        self.user.save()
        self.client.login(username=self.user.email, password='secret')

        self.mock_create_credit = self.patch(
            "finance.models.Payment.create_and_link_credit")
        self.mock_mail_confirmation = self.patch(
            "ordering.models.Order.mail_confirmation")
        self.mock_failure_notification = self.patch(
            "ordering.models.Order.mail_failure_notification")
        # TODO figure out why this mock breaks all ConfirmTransaction tests
        # self.mock_complete_after_payment = self.patch(
        #     "ordering.models.Order.complete_after_payment")

        class FakePaymentResult(object):
            checkout_url = "http://bank.url"

            def __getitem__(self, item):
                if item == "id":
                    return "transaction_id"

        self.mollie_client.return_value.payments.create.return_value = (
            FakePaymentResult())


class TestCreateTransaction(FinanceTestCase):
    def setUp(self):
        super(TestCreateTransaction, self).setUp()
        self.url = reverse('finance.createtransaction')

        self.order = OrderFactory(user=self.user,
                                  finalized=True,
                                  paid=False)

    def test_that_ideal_transaction_is_created(self):
        self.client.post(self.url, {'bank': 'EXAMPLE_BANK', 'method': "ideal"})
        self.mollie_client.return_value.payments.create.assert_called_once_with(  # noqa
            {'amount': {
                'currency': 'EUR',
                'value': "{0:.2f}".format(
                    self.order.total_price_to_pay_with_balances_taken_into_account())}, # noqa
                'description': 'VOKO Utrecht %d' % self.order.id,
                'webhookUrl': settings.BASE_URL + reverse('finance.callback'),
                'redirectUrl': (settings.BASE_URL
                                + reverse("finance.confirmtransaction")
                                + "?order=%d" % self.order.id),
                'metadata': {'order_id': self.order.id},
                'method': 'ideal',
                'issuer': 'EXAMPLE_BANK'}
        )

    def test_that_bancontact_transaction_is_created(self):
        self.client.post(self.url, {'method': "bancontact"})
        self.mollie_client.return_value.payments.create.assert_called_once_with(  # noqa
            {'amount': {
                'currency': 'EUR', 'value': "{0:.2f}".format( \
                    self.order.total_price_to_pay_with_balances_taken_into_account())}, # noqa
                'description': 'VOKO Utrecht %d' % self.order.id,
                'webhookUrl': settings.BASE_URL + reverse('finance.callback'),
                'redirectUrl': (settings.BASE_URL
                                + reverse("finance.confirmtransaction")
                                + "?order=%d" % self.order.id),
                'metadata': {'order_id': self.order.id},
                'method': 'bancontact',
                'issuer': None}
        )

    def test_that_payment_object_is_created_when_ideal(self):
        assert Payment.objects.count() == 0

        self.client.post(self.url, {'bank': "EXAMPLE_BANK",
                                    'method': "ideal"})
        payment = Payment.objects.get()

        self.assertEqual(
            payment.amount,
            self.order.total_price_to_pay_with_balances_taken_into_account()
        )
        self.assertEqual(payment.order, self.order)
        self.assertEqual(payment.mollie_id, "transaction_id")
        self.assertEqual(payment.balance, None)

    def test_that_payment_object_is_created_when_bancontact(self):
        assert Payment.objects.count() == 0

        self.client.post(self.url, {'method': "bancontact"})
        payment = Payment.objects.get()

        self.assertEqual(
            payment.amount,
            self.order.total_price_to_pay_with_balances_taken_into_account()
        )
        self.assertEqual(payment.order, self.order)
        self.assertEqual(payment.mollie_id, "transaction_id")
        self.assertEqual(payment.balance, None)

    def test_that_user_is_redirected_to_bank_url(self):
        ret = self.client.post(self.url, {'bank': "EXAMPLE_BANK",
                                          'method': "ideal"})
        self.assertEqual(ret.status_code, 302)
        self.assertEqual(ret.url, "http://bank.url")

    def test_redirect_when_order_not_finalized(self):
        # No order matches, so not found
        self.order.finalized = False
        self.order.save()

        ret = self.client.post(self.url, {'bank': "EXAMPLE_BANK",
                                          'method': "ideal"})
        self.assertRedirects(ret, reverse('view_products'))

    def test_redirect_when_order_round_is_closed(self):
        # No order matches, so not found
        month_ago = datetime.now(tz=UTC) - timedelta(days=30)
        order_round = OrderRoundFactory(closed_for_orders=month_ago)
        assert order_round.is_open is False
        self.order.order_round = order_round
        self.order.save()

        ret = self.client.post(self.url, {'bank': "EXAMPLE_BANK",
                                          'method': "ideal"})
        self.assertRedirects(ret, reverse('view_products'))


class TestConfirmTransaction(FinanceTestCase):
    def setUp(self):
        super(TestConfirmTransaction, self).setUp()
        self.url = reverse('finance.confirmtransaction')

        self.order = OrderFactory(user=self.user,
                                  finalized=True,
                                  paid=False)

        self.payment = PaymentFactory(order=self.order)
        self.client.login()

    @suppressWarnings
    def test_required_get_parameters_bad(self):
        ret = self.client.get(self.url, {})
        self.assertEqual(ret.status_code, 404)

    def test_required_get_parameters_good(self):
        ret = self.client.get(self.url, {"order": self.order.id})
        self.assertEqual(ret.status_code, 200)

    def test_mollie_payment_is_obtained(self):
        self.client.get(self.url, {"order": self.order.id})
        self.mollie_client.return_value.payments.get.assert_called_once_with(
            self.payment.mollie_id)

    def test_ispaid_is_called_on_mollie_payment(self):
        self.client.get(self.url, {"order": self.order.id})
        self.mollie_client.return_value.payments.get.\
            return_value.is_paid.assert_called_once_with()

    def test_context_when_payment_has_failed(self):
        self.mollie_client.return_value.payments.get.\
            return_value.is_paid.return_value = False
        ret = self.client.get(self.url, {"order": self.order.id})
        self.assertEqual(ret.context[0]['payment_succeeded'], False)

    def test_context_when_payment_has_succeeded(self):
        self.mollie_client.return_value.payments.get.\
            return_value.is_paid.return_value = True
        ret = self.client.get(self.url, {"order": self.order.id})
        self.assertEqual(ret.context[0]['payment_succeeded'], True)

    def test_payment_object_is_updated_on_success(self):
        self.assertFalse(self.payment.succeeded)

        self.mollie_client.return_value.payments.get. \
            return_value.is_paid.return_value = True
        self.client.get(self.url, {"order": self.order.id})

        # get new object reference
        payment = Payment.objects.get(id=self.payment.id)
        self.assertTrue(payment.succeeded)

    def test_payment_object_is_not_updated_on_failure(self):
        self.assertFalse(self.payment.succeeded)

        self.mollie_client.return_value.payments.get. \
            return_value.is_paid.return_value = False
        self.client.get(self.url, {"order": self.order.id})

        # get new object reference
        payment = Payment.objects.get(id=self.payment.id)
        self.assertFalse(payment.succeeded)

    def test_payment_and_order_status_after_successful_payment(self):
        self.mollie_client.return_value.payments.get. \
            return_value.is_paid.return_value = True
        self.client.get(self.url, {"order": self.order.id})

        payment = Payment.objects.get()
        self.assertTrue(payment.succeeded)
        self.assertTrue(payment.order.paid)
        self.mock_create_credit.assert_called_once_with()

        debit = Balance.objects.get()
        self.assertEqual(debit.user, payment.order.user)
        self.assertEqual(debit.type, 'DR')
        self.assertEqual(debit.amount, payment.order.total_price)
        self.assertEqual(debit.notes, 'Debit van %s voor bestelling #%s' %
                         (payment.order.total_price, payment.order.id))
        self.mock_mail_confirmation.assert_called_once_with()

    def test_nothing_is_changed_when_payment_already_confirmed(self):
        self.order.paid = True
        self.order.save()
        self.client.get(self.url, {"order": self.order.id})

        ret = self.client.get(self.url, {"order": self.order.id})
        self.assertEqual(ret.context[0]['payment_succeeded'], True)

        self.assertFalse(self.mollie_client.return_value.payments.get.
                         return_value.is_paid.called)

        self.assertFalse(self.mock_create_credit.called)
        self.assertFalse(self.mock_mail_confirmation.called)


class TestPaymentWebhook(FinanceTestCase):
    def setUp(self):
        super(TestPaymentWebhook, self).setUp()

        self.order = OrderFactory(user=self.user,
                                  finalized=True,
                                  paid=False)
        self.payment = PaymentFactory(order=self.order)

        self.url = reverse('finance.callback')

    @suppressWarnings
    def test_required_post_parameters_bad(self):
        ret = self.client.post(self.url, {})
        self.assertEqual(ret.status_code, 404)

    def test_required_post_parameters_good(self):
        ret = self.client.post(self.url, {"id": self.payment.mollie_id})
        self.assertEqual(ret.status_code, 200)

    def test_unsuccessful_payment(self):
        self.mollie_client.return_value.payments.get. \
            return_value.is_paid.return_value = False
        ret = self.client.post(self.url, {"id": self.payment.mollie_id})

        payment = Payment.objects.get(id=self.payment.id)
        self.assertFalse(payment.succeeded)
        self.assertFalse(self.mock_create_credit.called)
        self.assertFalse(payment.order.paid)
        self.assertFalse(payment.order.debit)
        self.assertFalse(self.mock_mail_confirmation.called)
        # self.assertFalse(self.mock_complete_after_payment.called)

        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.content, b"")

    def test_successful_payment(self):
        self.mollie_client.return_value.payments.get. \
            return_value.is_paid.return_value = True
        ret = self.client.post(self.url, {"id": self.payment.mollie_id})

        payment = Payment.objects.get(id=self.payment.id)
        self.assertTrue(payment.succeeded)
        self.assertTrue(self.mock_create_credit.called)
        self.assertTrue(payment.order.paid)
        self.assertTrue(payment.order.debit)
        self.assertTrue(self.mock_mail_confirmation.called)
        # self.mock_complete_after_payment.assert_called_once_with()

        self.assertEqual(ret.status_code, 200)
        self.assertEqual(ret.content, b"")

    def test_order_is_completed_when_order_paid_is_false(self):
        assert self.order.paid is False
        self.mollie_client.return_value.payments.get. \
            return_value.is_paid.return_value = True
        self.client.post(self.url, {"id": self.payment.mollie_id})

        # self.mock_complete_after_payment.assert_called_once_with()

    def test_order_is_not_completed_when_round_is_closed_and_notification_is_sent(self):  # noqa
        month_ago = datetime.now(tz=UTC) - timedelta(days=30)
        order_round = OrderRoundFactory(closed_for_orders=month_ago)
        assert order_round.is_open is False
        self.order.order_round = order_round
        self.order.save()

        assert self.order.paid is False

        self.mollie_client.return_value.payments.get. \
            return_value.is_paid.return_value = True
        self.client.post(self.url, {"id": self.payment.mollie_id})

        payment = Payment.objects.get()
        self.assertFalse(payment.order.paid)
        self.mock_create_credit.assert_called_once_with()
        # self.assertFalse(self.mock_complete_after_payment.called)

        self.mock_failure_notification.assert_called_once_with()


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

    def test_order_finalized_is_set_to_false(self):
        self.client.get(self.url)
        order = Order.objects.get()
        self.assertFalse(order.finalized)

    def test_redirect_to_finish_order(self):
        ret = self.client.get(self.url)
        self.assertRedirects(ret, "%s" %
                             reverse('finish_order', args=(self.order.id,)),
                             fetch_redirect_response=False)
