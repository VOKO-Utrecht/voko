from vokou.testing import VokoTestCase
from ordering.cron import SendPickupReminders
from datetime import datetime, timedelta
from pytz import UTC
from mock import patch
from ordering.tests.factories import OrderRoundFactory


class TestPickupReminderJob(VokoTestCase):

    def test_pickup_reminder_send(self):
        with patch(
            "ordering.models.OrderRound.send_pickup_reminder_mails") as \
                mock_mail:
            now = datetime.now(tz=UTC)
            self.cur_order_round = OrderRoundFactory(
                open_for_orders=now - timedelta(days=4),
                closed_for_orders=now - timedelta(days=1),
                # Order collect time is within 3 hours
                collect_datetime=now + timedelta(hours=3))

            SendPickupReminders.do(self)
            mock_mail.assert_called_once()

    def test_pickup_reminder_not_send_too_early(self):
        with patch(
            "ordering.models.OrderRound.send_pickup_reminder_mails") as \
                mock_mail:
            now = datetime.now(tz=UTC)
            self.cur_order_round = OrderRoundFactory(
                open_for_orders=now - timedelta(days=4),
                closed_for_orders=now - timedelta(days=1),
                # Order collect time is 12 hours away
                collect_datetime=now + timedelta(hours=12))

            SendPickupReminders.do(self)
            self.assertFalse(mock_mail.called)

    def test_pickup_reminder_not_send_too_late(self):
        with patch(
            "ordering.models.OrderRound.send_pickup_reminder_mails") as \
                mock_mail:
            now = datetime.now(tz=UTC)
            self.cur_order_round = OrderRoundFactory(
                open_for_orders=now - timedelta(days=4),
                closed_for_orders=now - timedelta(days=1),
                # Order collect time is 1 hour in the past
                collect_datetime=now - timedelta(hours=1))

            SendPickupReminders.do(self)
            self.assertFalse(mock_mail.called)
