from unittest import skip
from accounts.tests.factories import VokoUserFactory
from finance.models import Balance
from ordering.models import Order
from ordering.tests.factories import SupplierFactory, OrderFactory, OrderProductFactory, OrderRoundFactory
from vokou.testing import VokoTestCase


class TestSupplierModel(VokoTestCase):
    def setUp(self):
        self.supplier = SupplierFactory()
        self.order_round = OrderRoundFactory()

    @skip("todo: fix")
    def test_has_orders_returns_true_on_paid_orders(self):
        order = OrderFactory(finalized=True, paid=True, order_round=self.order_round)
        OrderProductFactory(order=order, product__supplier=self.supplier)
        self.assertTrue(self.supplier.has_orders_in_current_order_round())

    def test_has_orders_returns_false_on_non_paid_orders(self):
        order = OrderFactory(finalized=True, paid=False, order_round=self.order_round)
        OrderProductFactory(order=order, product__supplier=self.supplier)
        self.assertFalse(self.supplier.has_orders_in_current_order_round())


class TestOrderModel(VokoTestCase):
    def setUp(self):
        self.mock_mail_confirmation = self.patch("ordering.models.Order.mail_confirmation")

    def test_complete_after_payment_method(self):
        order = OrderFactory(paid=False, finalized=True)
        self.assertFalse(Balance.objects.exists())  # No debit created yet

        order.complete_after_payment()

        order = Order.objects.get()
        self.assertTrue(order.paid)

        debit = Balance.objects.get()
        self.assertEqual(debit.user, order.user)
        self.assertEqual(debit.type, 'DR')
        self.assertEqual(debit.amount, order.total_price)
        self.assertEqual(debit.notes, 'Debit van %s voor bestelling #%s' % (order.total_price, order.id))

        self.mock_mail_confirmation.assert_called_once_with()

    def test_user_order_number_with_one_paid_order(self):
        order = OrderFactory(paid=True, finalized=True)
        self.assertEqual(order.user_order_number, 1)

    def test_user_order_number_with_unpaid_order(self):
        order = OrderFactory(paid=False, finalized=True)
        self.assertEqual(order.user_order_number, None)

    def test_user_order_number_with_multiple_orders(self):
        user = VokoUserFactory()
        order1 = OrderFactory.create(paid=True, finalized=True, user=user)
        order2 = OrderFactory.create(paid=False, finalized=True, user=user)
        order3 = OrderFactory.create(paid=True, finalized=True, user=user)
        order4 = OrderFactory.create(paid=True, finalized=False, user=user)
        self.assertEqual(order1.user_order_number, 1)
        self.assertEqual(order2.user_order_number, None)
        self.assertEqual(order3.user_order_number, 2)
        self.assertEqual(order4.user_order_number, None)

    def test_user_order_number_with_multiple_orders_but_different_users(self):
        user1 = VokoUserFactory()
        user2 = VokoUserFactory()
        order1 = OrderFactory.create(paid=True, finalized=True, user=user1)
        order2 = OrderFactory.create(paid=True, finalized=True, user=user2)
        self.assertEqual(order1.user_order_number, 1)
        self.assertEqual(order2.user_order_number, 1)

