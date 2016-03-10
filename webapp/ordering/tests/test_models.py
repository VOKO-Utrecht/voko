from decimal import Decimal
from unittest import skip
from datetime import datetime, timedelta
from django.conf import settings
from mock import patch
from pytz import UTC
from accounts.tests.factories import VokoUserFactory
from finance.models import Balance
from finance.tests.factories import BalanceFactory
from ordering.models import Order, OrderProduct, ORDER_CONFIRM_MAIL_ID, ORDER_FAILED_ID
from ordering.tests.factories import SupplierFactory, OrderFactory, OrderProductFactory, OrderRoundFactory, \
    OrderProductCorrectionFactory
from vokou.testing import VokoTestCase


class TestSupplierModel(VokoTestCase):
    def setUp(self):
        self.supplier = SupplierFactory()
        self.order_round = OrderRoundFactory.create()

    @skip("Unable to figure out why this test won't succeed for now")
    def test_has_orders_returns_true_on_paid_orders(self):
        order = OrderFactory(finalized=True, paid=True, order_round=self.order_round)
        OrderProductFactory(order=order, product__supplier=self.supplier)

        # This all works...
        self.assertEqual(OrderProduct.objects.all()[0].order, order)
        self.assertEqual(OrderProduct.objects.all()[0].order.order_round, self.order_round)
        self.assertEqual(OrderProduct.objects.all()[0].product.supplier, self.supplier)

        # Something is going on with get_current_order_round, like it's mocked somewhere...
        self.assertTrue(self.supplier.has_orders_in_current_order_round())

    def test_has_orders_returns_false_on_non_paid_orders(self):
        order = OrderFactory(finalized=True, paid=False, order_round=self.order_round)
        OrderProductFactory(order=order, product__supplier=self.supplier)
        self.assertFalse(self.supplier.has_orders_in_current_order_round())


class TestOrderRoundModel(VokoTestCase):
    def setUp(self):
        now = datetime.now(tz=UTC)

        self.prev_order_round = OrderRoundFactory(open_for_orders=now - timedelta(days=8),
                                                  closed_for_orders=now - timedelta(days=4))
        self.cur_order_round = OrderRoundFactory(open_for_orders=now - timedelta(days=1),
                                                 closed_for_orders=now + timedelta(days=3))
        self.next_order_round = OrderRoundFactory(open_for_orders=now + timedelta(days=6),
                                                  closed_for_orders=now + timedelta(days=9))

    def test_is_not_open_yet(self):
        self.assertFalse(self.prev_order_round.is_not_open_yet())
        self.assertFalse(self.cur_order_round.is_not_open_yet())
        self.assertTrue(self.next_order_round.is_not_open_yet())

    def test_is_over(self):
        self.assertTrue(self.prev_order_round.is_over())
        self.assertFalse(self.cur_order_round.is_over())
        self.assertFalse(self.next_order_round.is_over())

    def test_is_open_property(self):
        self.assertFalse(self.prev_order_round.is_open)
        self.assertTrue(self.cur_order_round.is_open)
        self.assertFalse(self.next_order_round.is_open)

    @skip("This test also fails because some weird stuff with get_current_order_round")
    def test_is_current(self):
        self.assertFalse(self.prev_order_round.is_current())
        self.assertTrue(self.cur_order_round.is_current())
        self.assertFalse(self.next_order_round.is_current())

    def test_suppliers_with_no_orders(self):
        self.assertEqual(self.cur_order_round.suppliers(), [])

    def test_suppliers_with_paid_and_unpaid_orders(self):
        round = OrderRoundFactory()
        supplier1 = SupplierFactory()
        supplier2 = SupplierFactory()
        paid_order = OrderFactory(paid=True, finalized=True, order_round=round)
        finalized_order = OrderFactory(paid=False, finalized=True, order_round=round)
        supplier1_orderproduct = OrderProductFactory(product__supplier=supplier1, order=paid_order)
        supplier2_orderproduct = OrderProductFactory(product__supplier=supplier2, order=finalized_order)
        self.assertItemsEqual(round.suppliers(), [supplier1])

    def test_supplier_total_order_sum_with_one_order(self):
        round = OrderRoundFactory()
        supplier1 = SupplierFactory()
        paid_order = OrderFactory(paid=True, finalized=True, order_round=round)
        supplier1_orderproduct = OrderProductFactory(product__supplier=supplier1, order=paid_order)
        self.assertItemsEqual(round.suppliers(), [supplier1])

        self.assertEqual(round.supplier_total_order_sum(supplier1),
                         supplier1_orderproduct.product.base_price * supplier1_orderproduct.amount)

    def test_supplier_total_order_sum_with_multiple_orders(self):
        round = OrderRoundFactory()
        supplier1 = SupplierFactory()
        supplier1_orderproduct1 = OrderProductFactory(product__supplier=supplier1, order__order_round=round,
                                                      order__paid=True, order__finalized=True)
        supplier1_orderproduct2 = OrderProductFactory(product__supplier=supplier1, order__order_round=round,
                                                      order__paid=True, order__finalized=True)

        self.assertEqual(round.supplier_total_order_sum(supplier1),
                         (supplier1_orderproduct1.product.base_price * supplier1_orderproduct1.amount) +
                         (supplier1_orderproduct2.product.base_price * supplier1_orderproduct2.amount))

    def test_total_order_sum(self):
        round = OrderRoundFactory()
        orderproduct1 = OrderProductFactory(order__order_round=round,
                                            order__paid=True,
                                            order__finalized=True)
        orderproduct2 = OrderProductFactory(order__order_round=round,
                                            order__paid=True,
                                            order__finalized=True)
        orderproduct3 = OrderProductFactory(order__order_round=round,
                                            order__paid=False,
                                            order__finalized=False)

        self.assertEqual(round.total_order_sum(),
            (orderproduct1.product.base_price * orderproduct1.amount) +
            (orderproduct2.product.base_price * orderproduct2.amount))

    def test_total_corrections_with_no_corrections(self):
        round = OrderRoundFactory()
        self.assertEqual(round.total_corrections(),
            {'supplier_inc': 0, 'voko_inc': 0, 'supplier_exc': 0})

    def test_total_corrections(self):
        round = OrderRoundFactory()
        corr1 = OrderProductCorrectionFactory(order_product__order__order_round=round, charge_supplier=True)
        corr2 = OrderProductCorrectionFactory(order_product__order__order_round=round, charge_supplier=False)
        self.assertEqual(round.total_corrections(),
            {'supplier_inc': corr1.calculate_refund(),
             'voko_inc': corr2.calculate_refund(),
             'supplier_exc': corr1.calculate_supplier_refund()})

    def test_total_profit_without_corrections(self):
        round = OrderRoundFactory()
        orderprod1 = OrderProductFactory(order__order_round=round, order__paid=True)
        self.assertEqual(round.total_profit(), orderprod1.product.profit * orderprod1.amount)

    @skip("TODO: Think out logic")
    def test_total_profit_with_corrections(self):
        round = OrderRoundFactory()
        orderprod1 = OrderProductFactory(order__order_round=round, order__paid=True)
        ordercorr1 = OrderProductCorrectionFactory(order_product__order__order_round=round,
                                                   order_product__order__paid=True)
        # TODO: How do we handle (partly) lost profit of corrections?


class TestOrderModel(VokoTestCase):
    def setUp(self):
        self.get_template_by_id = self.patch("ordering.models.get_template_by_id")
        self.render_mail_template = self.patch("ordering.models.render_mail_template")
        self.mail_user = self.patch("ordering.models.mail_user")

    def test_complete_after_payment_method(self):
        with patch("ordering.models.Order.mail_confirmation") as mock_mail:
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

            mock_mail.assert_called_once_with()

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

    def test_has_products_with_no_products(self):
        order = OrderFactory()
        self.assertFalse(order.has_products)

    def test_has_products_with_one_orderproduct(self):
        order = OrderFactory()
        OrderProductFactory(order=order)
        self.assertTrue(order.has_products)

    def test_total_price_with_no_products(self):
        order = OrderFactory()
        self.assertEqual(order.total_price, order.member_fee + order.order_round.transaction_costs)

    def test_total_order_price_with_one_orderproduct(self):
        order = OrderFactory()
        odp1 = OrderProductFactory(order=order)
        self.assertEqual(order.total_price, (order.member_fee + order.order_round.transaction_costs) +
                         odp1.total_retail_price)

    def test_total_order_price_with_two_orderproducts(self):
        order = OrderFactory()
        odp1 = OrderProductFactory(order=order)
        odp2 = OrderProductFactory(order=order)
        self.assertEqual(order.total_price, (order.member_fee + order.order_round.transaction_costs) +
                         odp1.total_retail_price + odp2.total_retail_price)

    def test_total_price_to_pay_with_no_balance(self):
        order = OrderFactory()
        odp1 = OrderProductFactory(order=order)
        odp2 = OrderProductFactory(order=order)
        self.assertEqual(order.total_price_to_pay_with_balances_taken_into_account(),
                         order.total_price)

    def test_total_price_to_pay_with_credit(self):
        user = VokoUserFactory()
        BalanceFactory(user=user, type="CR", amount=0.10)
        order = OrderFactory(user=user)
        odp1 = OrderProductFactory(order=order)
        odp2 = OrderProductFactory(order=order)
        self.assertEqual(order.total_price_to_pay_with_balances_taken_into_account(),
                         order.total_price - Decimal("0.10"))

    def test_total_price_to_pay_with_more_credit_than_order_price(self):
        user = VokoUserFactory()
        BalanceFactory(user=user, type="CR", amount=100)
        order = OrderFactory(user=user)
        odp1 = OrderProductFactory(order=order, amount=1, product__base_price=10)
        self.assertEqual(order.total_price_to_pay_with_balances_taken_into_account(),
                         0)

    def test_total_price_to_pay_with_large_debit(self):
        user = VokoUserFactory()
        BalanceFactory(user=user, type="DR", amount=100)
        order = OrderFactory(user=user)
        odp1 = OrderProductFactory(order=order, amount=1, product__base_price=10)
        self.assertEqual(order.total_price_to_pay_with_balances_taken_into_account(),
                         order.total_price + Decimal("100"))

    def test_member_fee_on_first_order(self):
        order = OrderFactory()
        self.assertEqual(order.member_fee, settings.MEMBER_FEE)

    def test_member_fee_on_unpaid_orders(self):
        user = VokoUserFactory()
        order1 = OrderFactory(paid=False, user=user)
        order2 = OrderFactory(paid=False, user=user)
        order3 = OrderFactory(paid=False, user=user)

        self.assertEqual(order1.member_fee, settings.MEMBER_FEE)
        self.assertEqual(order2.member_fee, settings.MEMBER_FEE)
        self.assertEqual(order3.member_fee, settings.MEMBER_FEE)

    def test_member_fee_with_one_paid_order(self):
        user = VokoUserFactory()
        order1 = OrderFactory(paid=False, user=user)
        order2 = OrderFactory(paid=True, user=user)
        order3 = OrderFactory(paid=False, user=user)

        self.assertEqual(order1.member_fee, settings.MEMBER_FEE)
        self.assertEqual(order2.member_fee, settings.MEMBER_FEE)
        self.assertEqual(order3.member_fee, Decimal("0"))

    def test_create_debit(self):
        order = OrderFactory()
        odp1 = OrderProductFactory(order=order)
        self.assertIsNone(order.debit)
        order.create_debit()

        order = Order.objects.get()
        self.assertEqual(order.debit.user, order.user)
        self.assertEqual(order.debit.type, "DR")
        self.assertEqual(order.debit.amount, order.total_price)
        self.assertEqual(order.debit.notes, "Debit van %s voor bestelling #%d" % (order.total_price, order.id))

    def test_mail_confirmation(self):
        order = OrderFactory()
        order.mail_confirmation()

        self.get_template_by_id.assert_called_once_with(ORDER_CONFIRM_MAIL_ID)
        self.render_mail_template.assert_called_once_with(self.get_template_by_id.return_value,
                                                          user=order.user,
                                                          order=order)
        self.mail_user.assert_called_once_with(order.user)

    def test_mail_failure_notification(self):
        order = OrderFactory()
        order.mail_failure_notification()

        self.get_template_by_id.assert_called_once_with(ORDER_FAILED_ID)
        self.render_mail_template.assert_called_once_with(self.get_template_by_id.return_value,
                                                          user=order.user,
                                                          order=order)
        self.mail_user.assert_called_once_with(order.user)


class TestOrderProductModel(VokoTestCase):
    def test_total_retail_price(self):
        odp1 = OrderProductFactory()
        self.assertEqual(odp1.total_retail_price,
                         odp1.amount * odp1.product.retail_price)

    def test_total_cost_price(self):
        odp1 = OrderProductFactory()
        self.assertEqual(odp1.total_cost_price(),
                         odp1.amount * odp1.product.base_price)