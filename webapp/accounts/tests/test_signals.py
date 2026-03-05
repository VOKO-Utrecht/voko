from datetime import datetime, timedelta, time
from unittest import mock

import pytz
from django.test import TestCase

from accounts.tests.factories import VokoUserFactory, AddressFactory
from distribution.models import Shift
from ordering.models import OrderRound, PickupLocation
from transport.models import Route, Ride


class SleepingMemberSignalTest(TestCase):
    """Tests for the handle_member_set_to_sleeping signal handler."""

    def setUp(self):
        self.now = datetime.now(pytz.utc)
        self.address = AddressFactory.create()
        self.pickup_location = PickupLocation.objects.create(name="Test Location", address=self.address)
        self.future_order_round = OrderRound.objects.create(
            open_for_orders=self.now - timedelta(days=2),
            closed_for_orders=self.now - timedelta(days=1),
            collect_datetime=self.now + timedelta(days=7),
            pickup_location=self.pickup_location,
        )
        self.past_order_round = OrderRound.objects.create(
            open_for_orders=self.now - timedelta(days=10),
            closed_for_orders=self.now - timedelta(days=9),
            collect_datetime=self.now - timedelta(days=7),
            pickup_location=self.pickup_location,
        )
        self.route = Route.objects.create(name="Test Route")
        self.member = VokoUserFactory.create()
        self.coordinator = VokoUserFactory.create()

    def _make_future_shift(self, coordinator=None):
        shift = Shift.objects.create(
            order_round=self.future_order_round,
            start=time(14, 0),
            end=time(16, 0),
        )
        shift.members.add(self.member)
        if coordinator:
            self.future_order_round.distribution_coordinator = coordinator
            self.future_order_round.save()
        return shift

    def _make_past_shift(self):
        shift = Shift.objects.create(
            order_round=self.past_order_round,
            start=time(14, 0),
            end=time(16, 0),
        )
        shift.members.add(self.member)
        return shift

    def _make_future_ride(self, as_driver=True, coordinator=None):
        other_user = VokoUserFactory.create()
        ride = Ride.objects.create(
            order_round=self.future_order_round,
            route=self.route,
            driver=self.member if as_driver else other_user,
            codriver=other_user if as_driver else self.member,
        )
        if coordinator:
            self.future_order_round.transport_coordinator = coordinator
            self.future_order_round.save()
        return ride

    def _member_in_shift(self, shift):
        return Shift.members.through.objects.filter(
            shift=shift, vokouser_id=self.member.pk
        ).exists()

    def test_member_removed_from_future_shift_when_set_to_sleeping(self):
        shift = self._make_future_shift()
        self.assertTrue(self._member_in_shift(shift))

        self.member.is_asleep = True
        self.member.save()

        self.assertFalse(self._member_in_shift(shift))

    def test_member_not_removed_from_past_shift_when_set_to_sleeping(self):
        shift = self._make_past_shift()
        self.assertTrue(self._member_in_shift(shift))

        self.member.is_asleep = True
        self.member.save()

        self.assertTrue(self._member_in_shift(shift))

    @mock.patch("accounts.signals.send_mail")
    def test_coordinator_notified_when_member_removed_from_shift(self, mock_send_mail):
        self._make_future_shift(coordinator=self.coordinator)

        self.member.is_asleep = True
        self.member.save()

        mock_send_mail.assert_called_once()
        call_kwargs = mock_send_mail.call_args
        self.assertIn(self.coordinator.email, call_kwargs[1]["recipient_list"])

    @mock.patch("accounts.signals.mail_admins")
    def test_admins_notified_when_no_shift_coordinator(self, mock_mail_admins):
        self._make_future_shift(coordinator=None)

        self.member.is_asleep = True
        self.member.save()

        mock_mail_admins.assert_called_once()

    @mock.patch("accounts.signals.send_mail")
    def test_coordinator_notified_when_member_is_ride_driver(self, mock_send_mail):
        self._make_future_ride(as_driver=True, coordinator=self.coordinator)

        self.member.is_asleep = True
        self.member.save()

        mock_send_mail.assert_called_once()
        call_kwargs = mock_send_mail.call_args
        self.assertIn(self.coordinator.email, call_kwargs[1]["recipient_list"])

    @mock.patch("accounts.signals.send_mail")
    def test_coordinator_notified_when_member_is_ride_codriver(self, mock_send_mail):
        self._make_future_ride(as_driver=False, coordinator=self.coordinator)

        self.member.is_asleep = True
        self.member.save()

        mock_send_mail.assert_called_once()
        call_kwargs = mock_send_mail.call_args
        self.assertIn(self.coordinator.email, call_kwargs[1]["recipient_list"])

    @mock.patch("accounts.signals.send_mail")
    def test_no_notification_when_already_sleeping(self, mock_send_mail):
        self._make_future_shift()
        self.member.is_asleep = True
        self.member.save()
        mock_send_mail.reset_mock()

        # Save again while already sleeping - should not trigger again
        self.member.save()
        mock_send_mail.assert_not_called()

    @mock.patch("accounts.signals.send_mail")
    def test_no_notification_when_waking_up(self, mock_send_mail):
        """Setting is_asleep=False should not trigger notifications."""
        self._make_future_shift()
        # Bypass signal to set sleeping state directly
        from accounts.models import VokoUser
        VokoUser.objects.filter(pk=self.member.pk).update(is_asleep=True)

        self.member.refresh_from_db()
        self.member.is_asleep = False
        self.member.save()

        mock_send_mail.assert_not_called()

    @mock.patch("accounts.signals.mail_admins")
    def test_admins_notified_when_no_ride_coordinator(self, mock_mail_admins):
        self._make_future_ride(as_driver=True, coordinator=None)

        self.member.is_asleep = True
        self.member.save()

        mock_mail_admins.assert_called_once()
