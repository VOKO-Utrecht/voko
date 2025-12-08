from vokou.testing import VokoTestCase
from ordering.cron import SendPickupReminders, MailOrderLists
from datetime import datetime, timedelta
from pytz import UTC
from unittest.mock import patch
from ordering.tests.factories import OrderFactory, OrderProductFactory, OrderRoundFactory, ProductFactory


class TestPickupReminderJob(VokoTestCase):
    def test_pickup_reminder_send(self):
        with patch("ordering.models.OrderRound.send_pickup_reminder_mails") as mock_mail:
            now = datetime.now(tz=UTC)
            self.cur_order_round = OrderRoundFactory(
                open_for_orders=now - timedelta(days=4),
                closed_for_orders=now - timedelta(days=1),
                # Order collect time is within 3 hours
                collect_datetime=now + timedelta(hours=3),
            )

            SendPickupReminders.do(self)
            mock_mail.assert_called_once()

    def test_pickup_reminder_not_send_too_early(self):
        with patch("ordering.models.OrderRound.send_pickup_reminder_mails") as mock_mail:
            now = datetime.now(tz=UTC)
            self.cur_order_round = OrderRoundFactory(
                open_for_orders=now - timedelta(days=4),
                closed_for_orders=now - timedelta(days=1),
                # Order collect time is 12 hours away
                collect_datetime=now + timedelta(hours=12),
            )

            SendPickupReminders.do(self)
            self.assertFalse(mock_mail.called)

    def test_pickup_reminder_not_send_too_late(self):
        with patch("ordering.models.OrderRound.send_pickup_reminder_mails") as mock_mail:
            now = datetime.now(tz=UTC)
            self.cur_order_round = OrderRoundFactory(
                open_for_orders=now - timedelta(days=4),
                closed_for_orders=now - timedelta(days=1),
                # Order collect time is 1 hour in the past
                collect_datetime=now - timedelta(hours=1),
            )

            SendPickupReminders.do(self)
            self.assertFalse(mock_mail.called)

    def test_mail_order_list(self):
        with patch("django.core.mail.EmailMultiAlternatives.send") as mock_mail:
            now = datetime.now(tz=UTC)
            self.order_round = OrderRoundFactory(
                open_for_orders=now - timedelta(days=4),
                closed_for_orders=now - timedelta(days=1),
                collect_datetime=now + timedelta(hours=1),
            )
            product = ProductFactory(order_round=self.order_round, maximum_total_order=10)
            order1 = OrderFactory(order_round=self.order_round, finalized=True, paid=True)
            OrderProductFactory(order=order1, product=product, amount=10)

            MailOrderLists.do(self)
            self.assertTrue(mock_mail.called)
