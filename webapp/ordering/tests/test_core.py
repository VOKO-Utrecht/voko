from datetime import datetime, timedelta
from pytz import UTC
from freezegun import freeze_time
from constance import config
from ordering.core import (
    get_current_order_round,
    get_latest_order_round,
    update_totals_for_products_with_max_order_amounts,
    create_orderround_ahead,
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
    def test_create_orderround_ahead_no_order_rounds_yet(self):
        """Test creating order rounds when no order rounds exist yet.

        Today is 2025-08-25 (Monday). With ORDERROUND_CREATE_DAYS_AHEAD=31,
        the horizon is 2025-09-25. Start date is 2025-09-01 (Monday +7 days),
        adjusted to next Sunday (ORDERROUND_OPEN_DAY_OF_WEEK=6): 2025-09-07.
        Rounds: 2025-09-07, 2025-09-21. Next (2025-10-05) exceeds horizon.
        """
        result = create_orderround_ahead()

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].open_for_orders.date(), datetime(2025, 9, 7).date())
        self.assertEqual(result[1].open_for_orders.date(), datetime(2025, 9, 21).date())

    @freeze_time("2025-08-25")
    def test_create_orderround_ahead_last_round_beyond_horizon(self):
        """Test that no rounds are created when the last round is already beyond the horizon.

        Today is 2025-08-25, horizon is 2025-09-25.
        Last round opens on 2025-09-14 (Sunday). Next would be 2025-09-28, which exceeds horizon.
        """
        OrderRoundFactory(
            open_for_orders=datetime(2025, 9, 14, 12, 0, tzinfo=UTC),
            closed_for_orders=datetime(2025, 9, 17, 3, 0, tzinfo=UTC),
            collect_datetime=datetime(2025, 9, 17, 18, 0, tzinfo=UTC),
        )

        result = create_orderround_ahead()

        self.assertEqual(len(result), 0)

    @freeze_time("2025-08-25")
    def test_create_orderround_ahead_one_round_fits(self):
        """Test that exactly one round is created when only one fits within the horizon.

        Today is 2025-08-25, horizon is 2025-09-25.
        Last round opens on 2025-09-07 (Sunday). Next is 2025-09-21, which fits.
        The one after (2025-10-05) exceeds the horizon.
        """
        OrderRoundFactory(
            open_for_orders=datetime(2025, 9, 7, 12, 0, tzinfo=UTC),
            closed_for_orders=datetime(2025, 9, 9, 3, 0, tzinfo=UTC),
            collect_datetime=datetime(2025, 9, 9, 18, 0, tzinfo=UTC),
        )

        result = create_orderround_ahead()

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].open_for_orders.date(), datetime(2025, 9, 21).date())

    @freeze_time("2025-08-25")
    def test_create_orderround_ahead_uses_interval_weeks(self):
        """Test that new rounds use ORDERROUND_INTERVAL_WEEKS spacing from the last round."""
        existing_round = OrderRoundFactory(
            open_for_orders=datetime(2025, 9, 7, 12, 0, tzinfo=UTC),
            closed_for_orders=datetime(2025, 9, 9, 3, 0, tzinfo=UTC),
            collect_datetime=datetime(2025, 9, 9, 18, 0, tzinfo=UTC),
        )

        result = create_orderround_ahead()

        self.assertGreater(len(result), 0)
        expected_start = existing_round.open_for_orders.date() + timedelta(weeks=config.ORDERROUND_INTERVAL_WEEKS)
        self.assertEqual(result[0].open_for_orders.date(), expected_start)
