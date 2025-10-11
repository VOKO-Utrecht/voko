from datetime import datetime, timedelta
from pytz import UTC
from freezegun import freeze_time
from constance import config
from ordering.core import (
    get_current_order_round,
    get_latest_order_round,
    update_totals_for_products_with_max_order_amounts,
    create_orderround_batch,
)
from ordering.models import OrderProduct
from ordering.tests.factories import (
    OrderRoundFactory,
    OrderFactory,
    ProductFactory,
    OrderProductFactory,
    ProductStockFactory,
)
from vokou.testing import VokoTestCase


class TestGetCurrentOrderRound(VokoTestCase):
    def setUp(self):
        self.mock_datetime = self.patch("ordering.core.datetime")
        # Default return value
        self.mock_datetime.now.return_value = datetime.now(UTC)

    def test_given_no_order_rounds_function_returns_none(self):
        ret = get_current_order_round()
        self.assertIsNone(ret)

    def test_given_one_open_order_round_it_is_returned(self):
        self.mock_datetime.now.return_value = datetime(2014, 10, 28, 0, 0, tzinfo=UTC)
        orderround = OrderRoundFactory(
            open_for_orders=datetime(2014, 10, 27, 0, 0, tzinfo=UTC),
            closed_for_orders=datetime(2014, 10, 31, 19, 0, tzinfo=UTC),
            collect_datetime=datetime(2014, 11, 5, 17, 30, tzinfo=UTC),
        )
        ret = get_current_order_round()
        self.assertEqual(ret, orderround)

    def test_given_one_closed_order_round_it_is_returned(self):
        self.mock_datetime.now.return_value = datetime(2014, 11, 6, 0, 0, tzinfo=UTC)
        orderround = OrderRoundFactory(
            open_for_orders=datetime(2014, 10, 27, 0, 0, tzinfo=UTC),
            closed_for_orders=datetime(2014, 10, 31, 19, 0, tzinfo=UTC),
            collect_datetime=datetime(2014, 11, 5, 17, 30, tzinfo=UTC),
        )
        ret = get_current_order_round()
        self.assertEqual(ret, orderround)

    def test_given_previous_and_current_order_rounds_current_is_returned(self):
        OrderRoundFactory(
            open_for_orders=datetime(2014, 10, 27, 0, 0, tzinfo=UTC),
            closed_for_orders=datetime(2014, 10, 31, 19, 0, tzinfo=UTC),
            collect_datetime=datetime(2014, 11, 5, 17, 30, tzinfo=UTC),
        )
        current = OrderRoundFactory(
            open_for_orders=datetime(2014, 11, 10, 0, 0, tzinfo=UTC),
            closed_for_orders=datetime(2014, 11, 14, 19, 0, tzinfo=UTC),
            collect_datetime=datetime(2014, 11, 19, 17, 30, tzinfo=UTC),
        )
        self.mock_datetime.now.return_value = datetime(2014, 11, 15, 0, 0, tzinfo=UTC)

        ret = get_current_order_round()
        self.assertEqual(ret, current)

    def test_given_current_and_future_order_rounds_current_is_returned(self):
        current = OrderRoundFactory(
            open_for_orders=datetime(2014, 10, 27, 0, 0, tzinfo=UTC),
            closed_for_orders=datetime(2014, 10, 31, 19, 0, tzinfo=UTC),
            collect_datetime=datetime(2014, 11, 5, 17, 30, tzinfo=UTC),
        )
        OrderRoundFactory(
            open_for_orders=datetime(2014, 11, 10, 0, 0, tzinfo=UTC),
            closed_for_orders=datetime(2014, 11, 14, 19, 0, tzinfo=UTC),
            collect_datetime=datetime(2014, 11, 19, 17, 30, tzinfo=UTC),
        )
        self.mock_datetime.now.return_value = datetime(2014, 11, 4, 0, 0, tzinfo=UTC)

        ret = get_current_order_round()
        self.assertEqual(ret, current)

    def test_given_previous_and_future_rounds_future_round_is_returned(self):
        OrderRoundFactory(
            open_for_orders=datetime(2014, 10, 27, 0, 0, tzinfo=UTC),
            closed_for_orders=datetime(2014, 10, 31, 19, 0, tzinfo=UTC),
            collect_datetime=datetime(2014, 11, 5, 17, 30, tzinfo=UTC),
        )
        future = OrderRoundFactory(
            open_for_orders=datetime(2014, 11, 10, 0, 0, tzinfo=UTC),
            closed_for_orders=datetime(2014, 11, 14, 19, 0, tzinfo=UTC),
            collect_datetime=datetime(2014, 11, 19, 17, 30, tzinfo=UTC),
        )
        self.mock_datetime.now.return_value = datetime(2014, 11, 7, 0, 0, tzinfo=UTC)

        ret = get_current_order_round()
        self.assertEqual(ret, future)

    def test_given_multiple_future_rounds_the_first_one_is_returned(self):
        # December 12
        OrderRoundFactory(
            open_for_orders=datetime(2014, 12, 8, 0, 0, tzinfo=UTC),
            closed_for_orders=datetime(2014, 12, 12, 19, 0, tzinfo=UTC),
            collect_datetime=datetime(2014, 12, 17, 17, 30, tzinfo=UTC),
        )
        # October 24
        OrderRoundFactory(
            open_for_orders=datetime(2014, 11, 24, 0, 0, tzinfo=UTC),
            closed_for_orders=datetime(2014, 11, 28, 19, 0, tzinfo=UTC),
            collect_datetime=datetime(2014, 12, 3, 17, 30, tzinfo=UTC),
        )
        # October 10
        future1 = OrderRoundFactory(
            open_for_orders=datetime(2014, 11, 10, 0, 0, tzinfo=UTC),
            closed_for_orders=datetime(2014, 11, 14, 19, 0, tzinfo=UTC),
            collect_datetime=datetime(2014, 11, 19, 17, 30, tzinfo=UTC),
        )

        self.mock_datetime.now.return_value = datetime(2014, 11, 1, 0, 0, tzinfo=UTC)

        ret = get_current_order_round()
        self.assertEqual(ret, future1)

    def test_given_multiple_open_order_rounds_return_first_one(self):
        round1 = OrderRoundFactory()
        OrderRoundFactory()

        self.assertTrue(round1.is_open)
        self.assertEqual(get_current_order_round(), round1)


class TestUpdateOrderTotals(VokoTestCase):
    def setUp(self):
        self.round = OrderRoundFactory()
        self.order = OrderFactory(order_round=self.round)

    def test_that_sold_out_product_is_removed(self):
        product = ProductFactory(order_round=self.round, maximum_total_order=10)
        self.assertEqual(10, product.amount_available)

        order1 = OrderFactory(order_round=self.round, finalized=True, paid=True)
        OrderProductFactory(order=order1, product=product, amount=10)

        self.assertEqual(10, product.amount_ordered)
        self.assertEqual(0, product.amount_available)

        order2 = OrderFactory(order_round=self.round)
        OrderProductFactory(order=order2, amount=1)

        update_totals_for_products_with_max_order_amounts(order2)

        self.assertEqual(1, len(product.orderproducts.all()))

    def test_that_order_amount_is_decreased(self):
        # 10 available
        product = ProductFactory(order_round=self.round, maximum_total_order=10)
        self.assertEqual(10, product.amount_available)

        order1 = OrderFactory(order_round=self.round, finalized=True, paid=True)
        OrderProductFactory(order=order1, product=product, amount=8)

        # 8 ordered, leaves 2
        self.assertEqual(8, product.amount_ordered)
        self.assertEqual(2, product.amount_available)

        # attempt to order 5
        order2 = OrderFactory(order_round=self.round)
        order2_product = OrderProductFactory(order=order2, product=product, amount=5)

        update_totals_for_products_with_max_order_amounts(order2)

        # re-fetch, amount is decreased to remaining 2
        order2_product = OrderProduct.objects.get(pk=order2_product.pk)
        self.assertEqual(2, order2_product.amount)

    def test_sold_out_stock_product_is_removed(self):
        # 10 available
        product = ProductFactory(order_round=None)
        ProductStockFactory(product=product, amount=10)
        self.assertEqual(10, product.amount_available)

        order1 = OrderFactory(order_round=self.round, finalized=True, paid=True)
        OrderProductFactory(order=order1, product=product, amount=10)

        # 10 ordered, 0 remain
        self.assertEqual(10, product.amount_ordered)
        self.assertEqual(0, product.amount_available)

        # order 1 more
        order2 = OrderFactory(order_round=self.round)
        OrderProductFactory(order=order2, product=product, amount=1)

        self.assertEqual(2, len(product.orderproducts.all()))
        update_totals_for_products_with_max_order_amounts(order2)
        self.assertEqual(1, len(product.orderproducts.all()))

    def test_that_stock_product_amount_is_decreased(self):
        # 10 available
        product = ProductFactory(order_round=None)
        ProductStockFactory(product=product, amount=10)
        self.assertEqual(10, product.amount_available)

        order1 = OrderFactory(order_round=self.round, finalized=True, paid=True)
        OrderProductFactory(order=order1, product=product, amount=8)

        # 8 ordered, leaves 2
        self.assertEqual(8, product.amount_ordered)
        self.assertEqual(2, product.amount_available)

        # attempt to order 5
        order2 = OrderFactory(order_round=self.round)
        order2_product = OrderProductFactory(order=order2, product=product, amount=5)

        update_totals_for_products_with_max_order_amounts(order2)

        # re-fetch, amount is decreased to remaining 2
        order2_product = OrderProduct.objects.get(pk=order2_product.pk)
        self.assertEqual(2, order2_product.amount)


class TestGetLastOrderRound(VokoTestCase):
    def setUp(self):
        now = datetime.now(tz=UTC)

        # Creating in non-chronical order, to prevent accidentely getting
        # the correct next or previous order_round

        # The next order round
        self.next_order_round = OrderRoundFactory(
            open_for_orders=now + timedelta(days=6),
            closed_for_orders=now + timedelta(days=9),
            collect_datetime=now + timedelta(days=10),
        )
        # An old order round, to check previous round logic
        self.old_order_round = OrderRoundFactory(
            open_for_orders=now - timedelta(days=18),
            closed_for_orders=now - timedelta(days=14),
            collect_datetime=now - timedelta(days=13),
        )
        # The current rouder round
        self.cur_order_round = OrderRoundFactory(
            open_for_orders=now - timedelta(days=1),
            closed_for_orders=now + timedelta(days=3),
            collect_datetime=now + timedelta(days=4),
        )
        # A future order round, to check next round logic
        self.future_order_round = OrderRoundFactory(
            open_for_orders=now + timedelta(days=16),
            closed_for_orders=now + timedelta(days=19),
            collect_datetime=now + timedelta(days=20),
        )
        # The previous order round
        self.prev_order_round = OrderRoundFactory(
            open_for_orders=now - timedelta(days=8),
            closed_for_orders=now - timedelta(days=4),
            collect_datetime=now - timedelta(days=3),
        )

    def test_latest_order_round_is_returned(self):
        self.assertTrue(get_latest_order_round() == self.prev_order_round)
        self.assertFalse(get_latest_order_round() == self.cur_order_round)
        self.assertFalse(get_latest_order_round() == self.next_order_round)
        self.assertFalse(get_latest_order_round() == self.old_order_round)
        self.assertFalse(get_latest_order_round() == self.future_order_round)


class TestAutomaticOrderRoundCreation(VokoTestCase):
    @freeze_time("2025-08-25")
    def test_create_orderround_batch_no_order_rounds_yet(self):
        """Test creating order rounds when no order rounds exist yet"""
        # When there are no order rounds, should create from next week to end of next quarter
        result = create_orderround_batch()

        self.assertEqual(len(result), 2)  # Two order rounds should be created

    @freeze_time("2025-09-18")
    def test_create_orderround_batch_no_order_rounds_yet_next_quarter_close(self):
        """Test creating order rounds when no order rounds exist yet but next quarter is close"""
        # When there are no order rounds and next quarter is close, should create from next week to end of next quarter
        result = create_orderround_batch()

        self.assertEqual(len(result), 7)  # Seven order rounds should be created

    @freeze_time("2024-02-01")
    def test_create_orderround_batch_next_quarter_far_away(self):
        """Test when order rounds are planned for this quarter but next quarter is far away"""
        # Set test date to early February so next quarter (Q2) is more than 31 days away

        # Create order rounds that go close to end of Q1
        OrderRoundFactory(
            open_for_orders=datetime(2024, 3, 25, 8, 0, tzinfo=UTC),  # Near end of Q1
            closed_for_orders=datetime(2024, 3, 29, 8, 0, tzinfo=UTC),
            collect_datetime=datetime(2024, 4, 3, 18, 0, tzinfo=UTC),
        )

        result = create_orderround_batch()

        # Should not create any new order rounds since next quarter is far away
        # and current quarter is already covered
        self.assertEqual(len(result), 0)

    @freeze_time("2025-09-02")
    def test_create_orderround_batch_next_quarter_close(self):
        """Test when order rounds are planned for this quarter and next quarter is close"""
        # Set test date to late March so next quarter (Q2) is less than 31 days away

        # Create order rounds that go to end of Q1
        existing_round = OrderRoundFactory(
            open_for_orders=datetime(2025, 9, 28, 12, 0, tzinfo=UTC)  # Recent round in Q1
        )

        result = create_orderround_batch()

        # Should create order rounds for next quarter (Q2) since it's less than 31 days away
        self.assertGreater(len(result), 0)

        # New order rounds should start in Q2 (April 1, 2024 onwards)
        first_round = result[0]
        expected_start = existing_round.open_for_orders.date() + timedelta(weeks=config.ORDERROUND_INTERVAL_WEEKS)

        self.assertEqual(first_round.open_for_orders.date(), expected_start)
        # Should be in Q2 (April or later)
        self.assertGreaterEqual(first_round.open_for_orders.month, 10)
