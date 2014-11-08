import mock
from datetime import datetime
from django.test import TestCase
from pytz import UTC
from ordering.core import get_current_order_round
from ordering.models import OrderRound


class VokoTestCase(TestCase):
    def patch(self, to_patch):
        patcher = mock.patch(to_patch)
        self.addCleanup(patcher.stop)
        return patcher.start()


class TestGetCurrentOrderRound(VokoTestCase):
    def setUp(self):
        self.mock_datetime = self.patch("ordering.core.datetime")

    def test_given_no_order_rounds_function_returns_none(self):
        ret = get_current_order_round()
        self.assertIsNone(ret)

    def test_given_one_open_order_round_it_is_returned(self):
        self.mock_datetime.now.return_value = datetime(2014, 10, 28, 0, 0, tzinfo=UTC)
        orderround = OrderRound.objects.create(
            open_for_orders=datetime(2014, 10, 27, 0, 0, tzinfo=UTC),
            closed_for_orders=datetime(2014, 10, 31, 19, 0, tzinfo=UTC),
            collect_datetime=datetime(2014, 11, 5, 17, 30, tzinfo=UTC)
        )
        ret = get_current_order_round()
        self.assertEqual(ret, orderround)

    def test_given_one_closed_order_round_it_is_returned(self):
        self.mock_datetime.now.return_value = datetime(2014, 11, 6, 0, 0, tzinfo=UTC)
        orderround = OrderRound.objects.create(
            open_for_orders=datetime(2014, 10, 27, 0, 0, tzinfo=UTC),
            closed_for_orders=datetime(2014, 10, 31, 19, 0, tzinfo=UTC),
            collect_datetime=datetime(2014, 11, 5, 17, 30, tzinfo=UTC)
        )
        ret = get_current_order_round()
        self.assertEqual(ret, orderround)

    def test_given_a_previous_and_a_current_order_round_the_current_is_returned(self):
        previous = OrderRound.objects.create(
            open_for_orders=datetime(2014, 10, 27, 0, 0, tzinfo=UTC),
            closed_for_orders=datetime(2014, 10, 31, 19, 0, tzinfo=UTC),
            collect_datetime=datetime(2014, 11, 5, 17, 30, tzinfo=UTC)
        )
        current = OrderRound.objects.create(
            open_for_orders=datetime(2014, 11, 10, 0, 0, tzinfo=UTC),
            closed_for_orders=datetime(2014, 11, 14, 19, 0, tzinfo=UTC),
            collect_datetime=datetime(2014, 11, 19, 17, 30, tzinfo=UTC)
        )
        self.mock_datetime.now.return_value = datetime(2014, 11, 15, 0, 0, tzinfo=UTC)

        ret = get_current_order_round()
        self.assertEqual(ret, current)

    def test_given_a_current_and_a_future_order_round_the_current_is_returned(self):
        current = OrderRound.objects.create(
            open_for_orders=datetime(2014, 10, 27, 0, 0, tzinfo=UTC),
            closed_for_orders=datetime(2014, 10, 31, 19, 0, tzinfo=UTC),
            collect_datetime=datetime(2014, 11, 5, 17, 30, tzinfo=UTC)
        )
        future = OrderRound.objects.create(
            open_for_orders=datetime(2014, 11, 10, 0, 0, tzinfo=UTC),
            closed_for_orders=datetime(2014, 11, 14, 19, 0, tzinfo=UTC),
            collect_datetime=datetime(2014, 11, 19, 17, 30, tzinfo=UTC)
        )
        self.mock_datetime.now.return_value = datetime(2014, 11, 4, 0, 0, tzinfo=UTC)

        ret = get_current_order_round()
        self.assertEqual(ret, current)

    def test_given_a_previous_and_a_future_order_round_the_future_round_is_returned(self):
        previous = OrderRound.objects.create(
            open_for_orders=datetime(2014, 10, 27, 0, 0, tzinfo=UTC),
            closed_for_orders=datetime(2014, 10, 31, 19, 0, tzinfo=UTC),
            collect_datetime=datetime(2014, 11, 5, 17, 30, tzinfo=UTC)
        )
        future = OrderRound.objects.create(
            open_for_orders=datetime(2014, 11, 10, 0, 0, tzinfo=UTC),
            closed_for_orders=datetime(2014, 11, 14, 19, 0, tzinfo=UTC),
            collect_datetime=datetime(2014, 11, 19, 17, 30, tzinfo=UTC)
        )
        self.mock_datetime.now.return_value = datetime(2014, 11, 7, 0, 0, tzinfo=UTC)

        ret = get_current_order_round()
        self.assertEqual(ret, future)

    def test_given_multiple_future_rounds_the_first_one_is_returned(self):
        future3 = OrderRound.objects.create(
            open_for_orders=datetime(2014, 12, 8, 0, 0, tzinfo=UTC),
            closed_for_orders=datetime(2014, 12, 12, 19, 0, tzinfo=UTC),
            collect_datetime=datetime(2014, 12, 17, 17, 30, tzinfo=UTC)
        )

        future2 = OrderRound.objects.create(
            open_for_orders=datetime(2014, 11, 24, 0, 0, tzinfo=UTC),
            closed_for_orders=datetime(2014, 11, 28, 19, 0, tzinfo=UTC),
            collect_datetime=datetime(2014, 12, 3, 17, 30, tzinfo=UTC)
        )

        future1 = OrderRound.objects.create(
            open_for_orders=datetime(2014, 11, 10, 0, 0, tzinfo=UTC),
            closed_for_orders=datetime(2014, 11, 14, 19, 0, tzinfo=UTC),
            collect_datetime=datetime(2014, 11, 19, 17, 30, tzinfo=UTC)
        )

        self.mock_datetime.now.return_value = datetime(2014, 11, 1, 0, 0, tzinfo=UTC)

        ret = get_current_order_round()
        self.assertEqual(ret, future1)
