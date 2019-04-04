from decimal import Decimal
from unittest import skip
from datetime import datetime, timedelta
from django.conf import settings
from mock import patch
from pytz import UTC
from accounts.tests.factories import VokoUserFactory
from finance.models import Balance
from finance.tests.factories import BalanceFactory
from ordering.models import (
    Order, OrderProduct,
    OrderProductCorrection, OrderRound, Product, ProductStock)
from ordering.tests.factories import (
    SupplierFactory, OrderFactory, OrderProductFactory, OrderRoundFactory,
    OrderProductCorrectionFactory, ProductFactory, UnitFactory,
    ProductStockFactory)
from vokou.testing import VokoTestCase
from constance import config


class TestSupplierModel(VokoTestCase):
    def setUp(self):
        self.supplier = SupplierFactory()
        self.order_round = OrderRoundFactory.create()

    @skip("Unable to figure out why this test won't succeed for now")
    def test_has_orders_returns_true_on_paid_orders(self):
        order = OrderFactory(finalized=True, paid=True,
                             order_round=self.order_round)
        OrderProductFactory(order=order, product__supplier=self.supplier)

        # This all works...
        self.assertEqual(OrderProduct.objects.all()[0].order, order)
        self.assertEqual(OrderProduct.objects.all()[0].order.order_round,
                         self.order_round)
        self.assertEqual(OrderProduct.objects.all()[0].product.supplier,
                         self.supplier)

        # Something is going on with get_current_order_round,
        # like it's mocked somewhere...
        self.assertTrue(self.supplier.has_orders_in_current_order_round())

    def test_has_orders_returns_false_on_non_paid_orders(self):
        order = OrderFactory(finalized=True, paid=False,
                             order_round=self.order_round)
        OrderProductFactory(order=order, product__supplier=self.supplier)
        self.assertFalse(self.supplier.has_orders_in_current_order_round())

    def test_has_orders_ignores_stock_products(self):
        order = OrderFactory(finalized=True,
                             paid=True)
        OrderProductFactory(order=order,
                            product__supplier=self.supplier,
                            product__order_round=None)
        self.assertFalse(
            self.supplier.has_orders_in_current_order_round())


class TestOrderRoundModel(VokoTestCase):
    def setUp(self):
        now = datetime.now(tz=UTC)

        self.prev_order_round = OrderRoundFactory(
            open_for_orders=now - timedelta(days=8),
            closed_for_orders=now - timedelta(days=4))
        self.cur_order_round = OrderRoundFactory(
            open_for_orders=now - timedelta(days=1),
            closed_for_orders=now + timedelta(days=3))
        self.next_order_round = OrderRoundFactory(
            open_for_orders=now + timedelta(days=6),
            closed_for_orders=now + timedelta(days=9))

    def test_is_not_open_yet(self):
        self.assertFalse(self.prev_order_round.is_not_open_yet())
        self.assertFalse(self.cur_order_round.is_not_open_yet())
        self.assertTrue(self.next_order_round.is_not_open_yet())

    def test_is_over(self):
        self.assertTrue(self.prev_order_round.is_over)
        self.assertFalse(self.cur_order_round.is_over)
        self.assertFalse(self.next_order_round.is_over)

    def test_is_open_property(self):
        self.assertFalse(self.prev_order_round.is_open)
        self.assertTrue(self.cur_order_round.is_open)
        self.assertFalse(self.next_order_round.is_open)

    @skip(
        "This test also fails because some weird "
        "stuff with get_current_order_round")
    def test_is_current(self):
        self.assertFalse(self.prev_order_round.is_current())
        self.assertTrue(self.cur_order_round.is_current())
        self.assertFalse(self.next_order_round.is_current())

    def test_suppliers_with_no_orders(self):
        self.assertEqual(self.cur_order_round.suppliers(), [])

    def test_suppliers_with_paid_and_unpaid_orders(self):
        order_round = OrderRoundFactory()
        supplier1 = SupplierFactory()
        supplier2 = SupplierFactory()
        paid_order = OrderFactory(paid=True, finalized=True,
                                  order_round=order_round)
        finalized_order = OrderFactory(paid=False, finalized=True,
                                       order_round=order_round)
        OrderProductFactory(product__supplier=supplier1, order=paid_order)
        OrderProductFactory(product__supplier=supplier2, order=finalized_order)
        self.assertCountEqual(order_round.suppliers(), [supplier1])

    def test_supplier_total_order_sum_with_one_order(self):
        order_round = OrderRoundFactory()
        supplier1 = SupplierFactory()
        paid_order = OrderFactory(paid=True, finalized=True,
                                  order_round=order_round)
        supplier1_orderproduct = OrderProductFactory(
            product__supplier=supplier1, order=paid_order)
        self.assertCountEqual(order_round.suppliers(), [supplier1])

        self.assertEqual(order_round.supplier_total_order_sum(supplier1),
                         supplier1_orderproduct.product.base_price *
                         supplier1_orderproduct.amount)

    def test_supplier_total_order_sum_with_multiple_orders(self):
        order_round = OrderRoundFactory()
        supplier1 = SupplierFactory()
        supplier1_orderproduct1 = OrderProductFactory(
            product__supplier=supplier1, order__order_round=order_round,
            order__paid=True, order__finalized=True)
        supplier1_orderproduct2 = OrderProductFactory(
            product__supplier=supplier1, order__order_round=order_round,
            order__paid=True, order__finalized=True)

        expected_sum = (
            (supplier1_orderproduct1.product.base_price *
             supplier1_orderproduct1.amount)
            +
            (supplier1_orderproduct2.product.base_price *
             supplier1_orderproduct2.amount)
        )

        self.assertEqual(order_round.supplier_total_order_sum(supplier1),
                         expected_sum)

    def test_total_order_sum(self):
        order_round = OrderRoundFactory()
        orderproduct1 = OrderProductFactory(order__order_round=order_round,
                                            order__paid=True,
                                            order__finalized=True)
        orderproduct2 = OrderProductFactory(order__order_round=order_round,
                                            order__paid=True,
                                            order__finalized=True)
        # Not paid
        OrderProductFactory(order__order_round=order_round,
                            order__paid=False,
                            order__finalized=False)

        expected_sum = (
            (orderproduct1.product.base_price * orderproduct1.amount)
            +
            (orderproduct2.product.base_price * orderproduct2.amount)
        )

        self.assertEqual(order_round.total_order_sum(), expected_sum)

    def test_total_corrections_with_no_corrections(self):
        order_round = OrderRoundFactory()
        self.assertEqual(order_round.total_corrections(),
                         {'supplier_inc': 0, 'voko_inc': 0, 'supplier_exc': 0})

    def test_total_corrections(self):
        order_round = OrderRoundFactory()
        corr1 = OrderProductCorrectionFactory(
            order_product__order__order_round=order_round,
            charge_supplier=True)
        corr2 = OrderProductCorrectionFactory(
            order_product__order__order_round=order_round,
            charge_supplier=False)

        self.assertEqual(order_round.total_corrections(),
                         {'supplier_inc': corr1.calculate_refund(),
                          'voko_inc': corr2.calculate_refund(),
                          'supplier_exc': corr1.calculate_supplier_refund()})

    def test_total_profit_without_corrections(self):
        order_round = OrderRoundFactory()
        orderprod1 = OrderProductFactory(order__order_round=order_round,
                                         order__paid=True)
        self.assertEqual(order_round.total_profit(),
                         orderprod1.product.profit * orderprod1.amount)

    @skip("TODO: Think out logic")
    def test_total_profit_with_corrections(self):
        order_round = OrderRoundFactory()
        OrderProductFactory(order__order_round=order_round,
                            order__paid=True)
        OrderProductCorrectionFactory(
            order_product__order__order_round=order_round,
            order_product__order__paid=True
        )
        # TODO: How do we handle (partly) lost profit of corrections?

    def test_number_of_orders_with_no_orders(self):
        order_round = OrderRoundFactory()
        self.assertEqual(order_round.number_of_orders(), 0)

    def test_number_of_orders_with_paid_and_unpaid_orders(self):
        order_round = OrderRoundFactory()
        # 3 paid
        OrderFactory(order_round=order_round, paid=True)
        OrderFactory(order_round=order_round, paid=True)
        OrderFactory(order_round=order_round, paid=True)
        # 2 unpaid
        OrderFactory(order_round=order_round, paid=False)
        OrderFactory(order_round=order_round, paid=False, finalized=True)

        self.assertEqual(order_round.number_of_orders(), 3)


class TestOrderModel(VokoTestCase):
    def setUp(self):
        self.get_template_by_id = self.patch(
            "ordering.models.get_template_by_id")
        self.render_mail_template = self.patch(
            "ordering.models.render_mail_template")
        self.mail_user = self.patch("ordering.models.mail_user")
        self.get_or_create_order = self.patch(
            "ordering.models.get_or_create_order")

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
            self.assertEqual(debit.notes,
                             'Debit van %.2f voor bestelling #%s' %
                             (order.total_price, order.id))

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
        self.assertEqual(order.total_price,
                         order.member_fee +
                         order.order_round.transaction_costs)

    def test_total_order_price_with_one_orderproduct(self):
        order = OrderFactory()
        odp1 = OrderProductFactory(order=order)
        self.assertEqual(order.total_price, (
                    order.member_fee + order.order_round.transaction_costs) +
                         odp1.total_retail_price)

    def test_total_order_price_with_two_orderproducts(self):
        order = OrderFactory()
        odp1 = OrderProductFactory(order=order)
        odp2 = OrderProductFactory(order=order)
        self.assertEqual(order.total_price, (
                    order.member_fee + order.order_round.transaction_costs) +
                         odp1.total_retail_price + odp2.total_retail_price)

    def test_total_price_to_pay_with_no_balance(self):
        order = OrderFactory()
        OrderProductFactory(order=order)
        OrderProductFactory(order=order)
        self.assertEqual(
            order.total_price_to_pay_with_balances_taken_into_account(),
            order.total_price)

    def test_total_price_to_pay_with_credit(self):
        user = VokoUserFactory()
        BalanceFactory(user=user, type="CR", amount=0.10)
        order = OrderFactory(user=user)
        OrderProductFactory(order=order)
        OrderProductFactory(order=order)
        self.assertEqual(
            order.total_price_to_pay_with_balances_taken_into_account(),
            order.total_price - Decimal("0.10"))

    def test_total_price_to_pay_with_more_credit_than_order_price(self):
        user = VokoUserFactory()
        BalanceFactory(user=user, type="CR", amount=100)
        order = OrderFactory(user=user)
        OrderProductFactory(order=order, amount=1, product__base_price=10)
        self.assertEqual(
            order.total_price_to_pay_with_balances_taken_into_account(),
            0)

    def test_total_price_to_pay_with_large_debit(self):
        user = VokoUserFactory()
        BalanceFactory(user=user, type="DR", amount=100)
        order = OrderFactory(user=user)
        OrderProductFactory(order=order, amount=1, product__base_price=10)
        self.assertEqual(
            order.total_price_to_pay_with_balances_taken_into_account(),
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
        OrderProductFactory(order=order)
        self.assertIsNone(order.debit)
        order.create_debit()

        order = Order.objects.get()
        self.assertEqual(order.debit.user, order.user)
        self.assertEqual(order.debit.type, "DR")
        self.assertEqual(order.debit.amount, order.total_price)
        self.assertEqual(order.debit.notes,
                         "Debit van %s voor bestelling #%d" %
                         (order.total_price, order.id))

    def test_mail_confirmation(self):
        order = OrderFactory()
        order.mail_confirmation()

        self.get_template_by_id.assert_called_once_with(config.ORDER_CONFIRM_MAIL)
        self.render_mail_template.assert_called_once_with(
            self.get_template_by_id.return_value,
            user=order.user,
            order=order)
        self.mail_user.assert_called_once_with(order.user)

    def test_mail_failure_notification(self):
        order = OrderFactory()
        order.mail_failure_notification()

        self.get_template_by_id.assert_called_once_with(config.ORDER_FAILED_MAIL)
        self.render_mail_template.assert_called_once_with(
            self.get_template_by_id.return_value,
            user=order.user,
            order=order)
        self.mail_user.assert_called_once_with(order.user)

    def test_ordermanager_get_current_order_1(self):
        order = OrderFactory(paid=False)
        self.assertEqual(order.user.orders.get_current_order(), order)

    def test_ordermanager_get_current_order_2(self):
        order = OrderFactory(paid=True)
        self.assertEqual(len(Order.objects.all()), 1)

        order.user.orders.get_current_order()
        self.get_or_create_order.assert_called_once_with(user=order.user)
        self.assertEqual(order.user.orders.get_current_order(),
                         self.get_or_create_order.return_value)

    def test_ordermanager_get_last_paid_order_1(self):
        order = OrderFactory(paid=False)
        self.assertIsNone(order.user.orders.get_last_paid_order())

    def test_ordermanager_get_last_paid_order_2(self):
        order = OrderFactory(paid=True)
        self.assertEqual(order.user.orders.get_last_paid_order(), order)


class TestOrderProductModel(VokoTestCase):
    def test_total_retail_price(self):
        odp1 = OrderProductFactory()
        self.assertEqual(odp1.total_retail_price,
                         odp1.amount * odp1.product.retail_price)

    def test_total_cost_price(self):
        odp1 = OrderProductFactory()
        self.assertEqual(odp1.total_cost_price(),
                         odp1.amount * odp1.product.base_price)


class TestProductModel(VokoTestCase):
    def test_unit_of_measurement(self):
        product = ProductFactory()
        self.assertEqual(product.unit_of_measurement, "%s %s" % (
            product.unit_amount, product.unit.description.lower()))

    def test_retail_price_1(self):
        product = ProductFactory(base_price=10,
                                 order_round__markup_percentage=10)
        self.assertEqual(product.retail_price, Decimal("11"))

    def test_retail_price_2(self):
        product = ProductFactory(base_price=10.50,
                                 order_round__markup_percentage=7)
        self.assertEqual(product.retail_price, Decimal("11.24"))

    def test_retail_price_3(self):
        product = ProductFactory(base_price=10.50,
                                 order_round__markup_percentage=0)
        self.assertEqual(product.retail_price, Decimal("10.50"))

    def test_amount_ordered_only_counts_orderproducts_of_paid_orders(self):
        product = ProductFactory()
        OrderProductFactory(product=product, order__paid=False)
        odp2 = OrderProductFactory(product=product, order__paid=True)
        odp3 = OrderProductFactory(product=product, order__paid=True)

        self.assertEqual(product.amount_ordered, odp2.amount + odp3.amount)

    def test_amount_ordered_with_no_orders(self):
        product = ProductFactory()
        self.assertEqual(product.amount_ordered, 0)

    def test_amount_available_when_no_max(self):
        product = ProductFactory(maximum_total_order=None)
        self.assertIsNone(product.amount_available)

    def test_amount_available_with_filled_max(self):
        product = ProductFactory(maximum_total_order=1)
        OrderProductFactory(product=product, order__paid=True, amount=1)
        self.assertEqual(product.amount_available, 0)

    def test_amount_available_with_max(self):
        product = ProductFactory(maximum_total_order=10)
        OrderProductFactory(product=product, order__paid=True, amount=1)
        self.assertEqual(product.amount_available, 9)

    def test_amount_available_with_stock_1(self):
        product = ProductFactory(maximum_total_order=None, order_round=None)
        stock1 = ProductStockFactory(product=product,
                                     type=ProductStock.TYPE_ADDED)
        stock2 = ProductStockFactory(product=product,
                                     type=ProductStock.TYPE_ADDED)
        self.assertEqual(product.amount_available,
                         (stock1.amount + stock2.amount))

    def test_amount_available_with_stock_2(self):
        product = ProductFactory(maximum_total_order=None, order_round=None)
        ProductStockFactory(product=product,
                            type=ProductStock.TYPE_ADDED, amount=10)
        ProductStockFactory(product=product,
                            type=ProductStock.TYPE_ADDED, amount=20),
        ProductStockFactory(product=product,
                            type=ProductStock.TYPE_LOST, amount=5),

        self.assertEqual(product.amount_available, 25)

    def test_amount_available_ignores_non_paid_orders(self):
        product = ProductFactory(maximum_total_order=10)
        OrderProductFactory(product=product, order__paid=False, amount=1)
        self.assertEqual(product.amount_available, 10)

    def test_percentage_available_with_no_max(self):
        product = ProductFactory(maximum_total_order=None)
        self.assertEqual(product.percentage_available, 100)

    def test_percentage_available_with_filled_max(self):
        product = ProductFactory(maximum_total_order=1)
        OrderProductFactory(product=product, order__paid=True, amount=1)
        self.assertEqual(product.percentage_available, 0)

    def test_percentage_available_with_max(self):
        product = ProductFactory(maximum_total_order=10)
        OrderProductFactory(product=product, order__paid=True, amount=1)
        self.assertEqual(product.percentage_available, 90)

    def test_percentage_available_ignores_non_paid_orders(self):
        product = ProductFactory(maximum_total_order=10)
        OrderProductFactory(product=product, order__paid=False, amount=1)
        self.assertEqual(product.percentage_available, 100)

    def test_percentage_available_is_rounded_to_int(self):
        product = ProductFactory(maximum_total_order=99)
        OrderProductFactory(product=product, order__paid=True, amount=25)
        self.assertEqual(product.percentage_available, 74)

    def test_percentage_available_with_stock_is_always_0(self):
        product = ProductFactory()
        ProductStockFactory(amount=10, product=product)
        OrderProductFactory(product=product, order__paid=True, amount=1)
        self.assertEqual(product.percentage_available, 100)

    def test_is_available_when_no_max(self):
        product = ProductFactory(maximum_total_order=None)
        self.assertTrue(product.is_available)

    def test_is_available_when_sold_out(self):
        product = ProductFactory(maximum_total_order=1)
        OrderProductFactory(product=product, order__paid=True, amount=1)
        self.assertFalse(product.is_available)

    def test_is_available_when_not_sold_out(self):
        product = ProductFactory(maximum_total_order=10)
        OrderProductFactory(product=product, order__paid=True, amount=1)
        self.assertTrue(product.is_available)

    def test_is_available_on_stock_product_1(self):
        product = ProductFactory(order_round=None)
        ProductStockFactory(product=product, amount=2)
        self.assertTrue(product.is_available)

    def test_is_available_on_stock_product_2(self):
        OrderRoundFactory()
        product = ProductFactory(order_round=None)
        ProductStockFactory(product=product, amount=5)
        ProductStockFactory(product=product, amount=4)
        OrderProductFactory(product=product, amount=9, order__paid=True)
        self.assertFalse(product.is_available)

    def test_creates_corrections_for_all_orderproducts_of_paid_orders(self):
        product = ProductFactory()
        paid_odp1 = OrderProductFactory(product=product, order__paid=True)
        paid_odp2 = OrderProductFactory(product=product, order__paid=True)
        # non paid
        OrderProductFactory(product=product, order__paid=False)

        self.assertCountEqual(OrderProductCorrection.objects.all(), [])
        product.create_corrections()

        corrections = OrderProductCorrection.objects.all().order_by('id')
        self.assertEqual(len(corrections), 2)

        self.assertEqual(corrections[0].order_product, paid_odp1)
        self.assertEqual(corrections[0].supplied_percentage, 0)
        self.assertEqual(corrections[0].notes,
                         'Product niet geleverd: "%s" (%s) [%s]' %
                         (paid_odp1.product.name,
                          paid_odp1.product.supplier.name,
                          paid_odp1.product.id))
        self.assertEqual(corrections[0].charge_supplier, True)

        self.assertEqual(corrections[1].order_product, paid_odp2)

    def test_determine_new_product_with_one_order_round(self):
        product = ProductFactory()
        self.assertEqual(len(OrderRound.objects.all()), 1)
        self.assertIsNone(product.determine_if_product_is_new_and_set_label())

    def test_determine_new_product_1(self):
        round1 = OrderRoundFactory()
        round2 = OrderRoundFactory()

        # Old, new
        ProductFactory(order_round=round1)
        new_product = ProductFactory(order_round=round2)

        self.assertFalse(new_product.new)
        new_product.determine_if_product_is_new_and_set_label()
        new_product = Product.objects.get(id=new_product.id)
        self.assertTrue(new_product.new)

    def test_determine_new_product_2(self):
        round1 = OrderRoundFactory()
        OrderRoundFactory()
        supplier = SupplierFactory()
        unit = UnitFactory()

        # old product
        ProductFactory(order_round=round1, name="Appels",
                       supplier=supplier, unit=unit)
        new_product = ProductFactory(order_round=round1, name="Appels",
                                     supplier=supplier, unit=unit)

        self.assertFalse(new_product.new)
        new_product.determine_if_product_is_new_and_set_label()
        new_product = Product.objects.get(id=new_product.id)
        self.assertFalse(new_product.new)

    def test_verbose_availability_1(self):
        product = ProductFactory(maximum_total_order=99)
        o1 = OrderProductFactory(product=product, order__paid=True).amount
        o2 = OrderProductFactory(product=product, order__paid=True).amount
        self.assertEqual(product.verbose_availability(),
                         "%s van 99" % (99 - (o1 + o2)))

    def test_verbose_availability_2(self):
        product = ProductFactory(maximum_total_order=None)
        self.assertEqual(product.verbose_availability(), "Onbeperkt")

    def test_verbose_availability_with_stock_1(self):
        product = ProductFactory(order_round=None)
        stock = ProductStockFactory(product=product,
                                    type=ProductStock.TYPE_ADDED)
        self.assertEqual(product.verbose_availability(),
                         "%s in voorraad" % stock.amount)

    def test_verbose_availability_with_stock_2(self):
        product = ProductFactory(order_round=None)
        stock1 = ProductStockFactory(product=product,
                                     type=ProductStock.TYPE_ADDED)
        stock2 = ProductStockFactory(product=product,
                                     type=ProductStock.TYPE_ADDED)
        self.assertEqual(product.verbose_availability(),
                         "%s in voorraad" % (stock1.amount + stock2.amount))

    def test_verbose_availability_with_stock_3(self):
        OrderRoundFactory()
        product = ProductFactory(order_round=None)
        stock1 = ProductStockFactory(product=product,
                                     type=ProductStock.TYPE_ADDED)
        stock2 = ProductStockFactory(product=product,
                                     type=ProductStock.TYPE_ADDED)
        odp1 = OrderProductFactory(product=product, amount=1, order__paid=True)

        self.assertEqual(product.verbose_availability(), "%s in voorraad" % (
                    (stock1.amount + stock2.amount) - odp1.amount))

    def test_verbose_availability_with_stock_4(self):
        OrderRoundFactory()
        product = ProductFactory(order_round=None)
        ProductStockFactory(product=product,
                            type=ProductStock.TYPE_ADDED, amount=10)
        ProductStockFactory(product=product,
                            type=ProductStock.TYPE_ADDED, amount=5)
        ProductStockFactory(product=product,
                            type=ProductStock.TYPE_LOST, amount=3)
        OrderProductFactory(product=product, amount=1, order__paid=True)

        self.assertEqual(product.verbose_availability(), "11 in voorraad")

    def test_verbose_availability_with_stock_sold_out(self):
        OrderRoundFactory()
        product = ProductFactory(order_round=None)
        stock = ProductStockFactory(product=product,
                                    type=ProductStock.TYPE_ADDED)
        OrderProductFactory(product=product, amount=stock.amount,
                            order__paid=True)

        self.assertEqual(product.verbose_availability(), "uitverkocht")


class TestOrderProductCorrectionModel(VokoTestCase):
    def test_creating_a_correction(self):
        order_product = OrderProductFactory.create()
        OrderProductCorrection.objects.create(order_product=order_product,
                                              supplied_percentage=0)

    def test_that_creating_a_correction_creates_sufficient_credit_1(self):
        order_product = OrderProductFactory.create(
            amount=10,
            product__base_price=Decimal('1'),
            product__order_round__markup_percentage=Decimal('7')
        )

        opc = OrderProductCorrection.objects.create(
            order_product=order_product,
            supplied_percentage=50)

        # Retail price is 1,07 per item
        # 10 items were ordered
        # 50% was delivered to member
        # so refund for 5 items.
        # 5 * 1,07 = 5,35
        expected_credit = Decimal('5.35')
        self.assertEqual(opc.credit.amount, expected_credit)

    def test_that_creating_a_correction_creates_sufficient_credit_2(self):
        order_product = OrderProductFactory.create(
            amount=10,
            product__base_price=Decimal('1'),
            product__order_round__markup_percentage=Decimal('7')
        )

        opc = OrderProductCorrection.objects.create(
            order_product=order_product,
            supplied_percentage=70
        )

        # Retail price is 1,07 per item
        # 10 items were ordered
        # 70% was delivered to member
        # so refund for 3 items.
        # 3 * 1,07 = 3,21
        expected_credit = Decimal('3.21')
        self.assertEqual(opc.credit.amount, expected_credit)

    def test_that_creating_a_correction_creates_sufficient_credit_3(self):
        order_product = OrderProductFactory.create(
            amount=10,
            product__base_price=Decimal(1),
            product__order_round__markup_percentage=Decimal(7)
        )

        opc = OrderProductCorrection.objects.create(
            order_product=order_product,
            supplied_percentage=0)

        self.assertEqual(opc.credit.amount,
                         Decimal(10 * 1.07).quantize(Decimal('.01')))

    def test_that_saving_order_correction_does_not_alter_the_credit(self):
        order_product = OrderProductFactory.create(
            amount=10,
            product__base_price=Decimal(1),
            product__order_round__markup_percentage=Decimal(7)
        )

        opc = OrderProductCorrection.objects.create(
            order_product=order_product,
            supplied_percentage=0)

        self.assertEqual(opc.credit.amount,
                         Decimal(10 * 1.07).quantize(Decimal('.01')))

        opc.supplied_percentage = 10
        opc.save()

        opc = OrderProductCorrection.objects.all().get()
        self.assertEqual(opc.credit.amount,
                         Decimal(10 * 1.07).quantize(Decimal('.01')))

    def test_that_creating_a_correction_creates_sufficient_credit_4(self):
        order_product = OrderProductFactory.create(
            amount=1,
            product__base_price=Decimal(1),
            product__order_round__markup_percentage=Decimal(7)
        )

        opc = OrderProductCorrection.objects.create(
            order_product=order_product,
            supplied_percentage=50)

        # Price is 1 Euro, markup is 7%, so total price is 1.07.
        # Half of 1.07 is 0.535
        # Rounding is ROUND_DOWN to 2 decimals, so 0.53.

        self.assertEqual(opc.credit.amount, Decimal('0.53'))

    def test_that_creating_a_correction_creates_sufficient_credit_5(self):
        order_product = OrderProductFactory.create(
            amount=2,
            product__base_price=Decimal(1),
            product__order_round__markup_percentage=Decimal(7)
        )

        opc = OrderProductCorrection.objects.create(
            order_product=order_product,
            supplied_percentage=45)

        # Price is 1 Euro, markup is 7%, amount is 2, so total price is 2.14.
        # 0.9 supplied, so 1.1 was not supplied.
        # 1.07 * 1.1 = 1.177
        # Rounding is ROUND_DOWN to 2 decimals, so 1.17.

        self.assertEqual(opc.credit.amount, Decimal('1.17'))

    def test_that_credit_description_is_filled_in(self):
        order_product = OrderProductFactory.create()
        opc = OrderProductCorrection.objects.create(
            order_product=order_product,
            supplied_percentage=0)
        self.assertEqual(opc.credit.notes,
                         "Correctie in ronde %d, %dx %s, geleverd: %s%%" %
                         (opc.order_product.product.order_round.id,
                          opc.order_product.amount,
                          opc.order_product.product.name,
                          opc.supplied_percentage))

    def test_calculate_refund_with_simple_values(self):
        order_round = OrderRoundFactory(markup_percentage=7)
        corr = OrderProductCorrectionFactory(
            order_product__order__order_round=order_round,
            order_product__product__order_round=order_round,
            order_product__product__base_price=10,
            order_product__amount=2,
            supplied_percentage=25)

        original_retail_price = corr.order_product.product.retail_price
        self.assertEqual(original_retail_price, Decimal('10.70'))

        self.assertEqual(corr.calculate_refund(), Decimal('16.05'))

    def test_calculate_refund_with_complex_values(self):
        order_round = OrderRoundFactory(markup_percentage=7.9)
        corr = OrderProductCorrectionFactory(
            order_product__order__order_round=order_round,
            order_product__product__order_round=order_round,
            order_product__product__base_price=9.95,
            order_product__amount=2,
            supplied_percentage=24)

        original_retail_price = corr.order_product.product.retail_price
        self.assertEqual(original_retail_price, Decimal('10.74'))

        self.assertEqual(corr.calculate_refund(), Decimal('16.32'))

    def test_calculate_refund_when_0_percent_supplied(self):
        order_round = OrderRoundFactory()
        corr = OrderProductCorrectionFactory(
            order_product__order__order_round=order_round,
            order_product__product__order_round=order_round,
            supplied_percentage=0)

        self.assertEqual(corr.calculate_refund(),
                         corr.order_product.total_retail_price)

    def test_calculate_supplier_refund_with_simple_values(self):
        order_round = OrderRoundFactory()
        corr = OrderProductCorrectionFactory(
            order_product__order__order_round=order_round,
            order_product__product__order_round=order_round,
            order_product__product__base_price=10,
            order_product__amount=2,
            supplied_percentage=25)

        self.assertEqual(corr.calculate_supplier_refund(), Decimal('15'))

    def test_supplier_refund_ignores_corrections_if_charge_supplier_is_false(
            self):
        order_round = OrderRoundFactory()
        corr = OrderProductCorrectionFactory(
            order_product__order__order_round=order_round,
            order_product__product__order_round=order_round,
            order_product__product__base_price=10,
            order_product__amount=2,
            supplied_percentage=25,
            charge_supplier=False)

        self.assertEqual(corr.calculate_supplier_refund(), Decimal('0'))

    def test_calculate_supplier_refund_with_complex_values(self):
        order_round = OrderRoundFactory()
        corr = OrderProductCorrectionFactory(
            order_product__order__order_round=order_round,
            order_product__product__order_round=order_round,
            order_product__product__base_price=9.95,
            order_product__amount=2,
            supplied_percentage=24)
        # Total price: 9.95 * 2 = 19.90
        # 19.90 * 0.76 = 15.12

        self.assertEqual(corr.calculate_supplier_refund(), Decimal('15.12'))

    def test_that_credit_is_created_on_save(self):
        self.assertFalse(Balance.objects.all().exists())
        corr = OrderProductCorrectionFactory()

        self.assertEqual(corr.credit.user, corr.order_product.order.user)
        self.assertEqual(corr.credit.amount, corr.calculate_refund())
        self.assertEqual(corr.credit.notes,
                         "Correctie in ronde %s, %dx %s, geleverd: %s%%" %
                         (corr.order_product.product.order_round.id,
                          corr.order_product.amount,
                          corr.order_product.product.name,
                          corr.supplied_percentage))

    def test_that_credit_is_not_overwritten_on_second_save(self):
        corr = OrderProductCorrectionFactory()
        credit_id = corr.credit.pk

        corr.save()

        corr = OrderProductCorrection.objects.get()
        self.assertEqual(corr.credit.pk, credit_id)

    def test_that_balance_is_removed_upon_deletion_of_single_item(self):
        corr = OrderProductCorrectionFactory()

        self.assertEqual(len(Balance.objects.all()), 1)
        corr.delete()
        self.assertEqual(len(Balance.objects.all()), 0)

    def test_that_balance_is_removed_upon_deletion_of_queryset(self):
        OrderProductCorrectionFactory()
        OrderProductCorrectionFactory()

        self.assertEqual(len(Balance.objects.all()), 2)
        OrderProductCorrection.objects.all().delete()
        self.assertEqual(len(Balance.objects.all()), 0)


class TestProductStockModel(VokoTestCase):
    def test_changing_amount_is_prohibited(self):
        ps = ProductStockFactory()

        ps.amount += 1

        with self.assertRaises(AssertionError):
            ps.save()

    def test_changing_type_is_prohibited(self):
        ps = ProductStockFactory(type='added')

        ps.type = 'lost'

        with self.assertRaises(AssertionError):
            ps.save()

    def test_changing_product_is_prohibited(self):
        ps = ProductStockFactory(type='added')

        ps.product = ProductFactory()

        with self.assertRaises(AssertionError):
            ps.save()

    def test_regular_save(self):
        ps = ProductStockFactory()
        ps.save()
