from django.conf import settings
from vokou.testing import VokoTestCase
from ordering.cron import SendPickupReminders, MailOrderLists
from datetime import datetime, timedelta
from pytz import UTC
from mock import patch, MagicMock
from ordering.tests.factories import (
    OrderFactory,
    OrderProductFactory,
    OrderRoundFactory,
    ProductFactory,
)


class TestPickupReminderJob(VokoTestCase):
    def test_pickup_reminder_send(self):
        with patch(
            "ordering.models.OrderRound.send_pickup_reminder_mails"
        ) as mock_mail:
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
        with patch(
            "ordering.models.OrderRound.send_pickup_reminder_mails"
        ) as mock_mail:
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
        with patch(
            "ordering.models.OrderRound.send_pickup_reminder_mails"
        ) as mock_mail:
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
        with patch("ordering.cron.EmailMultiAlternatives") as mock_email_class:
            mock_msg = MagicMock()
            mock_email_class.return_value = mock_msg

            now = datetime.now(tz=UTC)
            self.order_round = OrderRoundFactory(
                open_for_orders=now - timedelta(days=4),
                closed_for_orders=now - timedelta(days=1),
                collect_datetime=now + timedelta(hours=1),
            )
            product = ProductFactory(
                order_round=self.order_round, maximum_total_order=10
            )
            order1 = OrderFactory(
                order_round=self.order_round, finalized=True, paid=True
            )
            OrderProductFactory(order=order1, product=product, amount=10)

            MailOrderLists.do(self)

            # Verify email was sent
            self.assertTrue(mock_msg.send.called)

            # Verify organization settings are used in email
            call_args = mock_email_class.call_args
            subject = call_args[0][0]
            from_email = call_args[0][2]

            # Subject should contain organization name
            self.assertIn(settings.ORGANIZATION_NAME, subject)

            # From email should contain organization name and supplier email
            self.assertIn(settings.ORGANIZATION_NAME, from_email)
            self.assertIn(settings.ORGANIZATION_SUPPLIER_EMAIL, from_email)

            # Attachment filename should contain org slug
            attach_call_args = mock_msg.attach.call_args
            filename = attach_call_args[0][0]
            org_slug = settings.ORGANIZATION_SHORT_NAME.lower().replace(" ", "_")
            self.assertIn(org_slug, filename)
