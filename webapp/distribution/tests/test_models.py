# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, time
from unittest import mock

import pytz
from django.test import TestCase
from django.utils.text import slugify

from distribution.models import Shift
from ordering.models import OrderRound, PickupLocation
from accounts.tests.factories import VokoUserFactory, AddressFactory
from vokou.testing import VokoTestCase


class ShiftModelTest(TestCase):
    """Tests for the Shift model."""

    def setUp(self):
        """Set up test data."""
        self.now = datetime.now(pytz.utc)
        self.address = AddressFactory.create()
        self.pickup_location = PickupLocation.objects.create(
            name="Test Location",
            address=self.address
        )
        self.order_round = OrderRound.objects.create(
            open_for_orders=self.now - timedelta(days=2),
            closed_for_orders=self.now - timedelta(days=1),
            collect_datetime=self.now + timedelta(days=1),
            pickup_location=self.pickup_location
        )

    def test_str_representation(self):
        """Test string representation of Shift."""
        shift = Shift.objects.create(
            order_round=self.order_round,
            start=time(14, 0),
            end=time(16, 0)
        )
        # Format: date-start-end
        expected = "{}-{}-{}".format(
            self.order_round.collect_datetime.strftime("%Y-%m-%d"),
            "14:00",
            "16:00"
        )
        self.assertEqual(str(shift), expected)

    def test_slug_generated_on_save(self):
        """Test slug is auto-generated."""
        shift = Shift.objects.create(
            order_round=self.order_round,
            start=time(14, 0),
            end=time(16, 0)
        )
        self.assertIsNotNone(shift.slug)
        self.assertTrue(len(shift.slug) > 0)

    def test_date_property(self):
        """Test date property returns order_round collect_datetime."""
        shift = Shift.objects.create(
            order_round=self.order_round,
            start=time(14, 0),
            end=time(16, 0)
        )
        self.assertEqual(shift.date, self.order_round.collect_datetime)

    def test_date_str_property(self):
        """Test date_str property returns formatted date."""
        shift = Shift.objects.create(
            order_round=self.order_round,
            start=time(14, 0),
            end=time(16, 0)
        )
        expected = self.order_round.collect_datetime.strftime("%Y-%m-%d")
        self.assertEqual(shift.date_str, expected)

    def test_start_str_property(self):
        """Test start_str property returns formatted time."""
        shift = Shift.objects.create(
            order_round=self.order_round,
            start=time(14, 30),
            end=time(16, 0)
        )
        self.assertEqual(shift.start_str, "14:30")

    def test_end_str_property(self):
        """Test end_str property returns formatted time."""
        shift = Shift.objects.create(
            order_round=self.order_round,
            start=time(14, 0),
            end=time(16, 30)
        )
        self.assertEqual(shift.end_str, "16:30")

    def test_distribution_coordinator_property(self):
        """Test distribution_coordinator returns from order_round."""
        coordinator = VokoUserFactory.create()
        self.order_round.distribution_coordinator = coordinator
        self.order_round.save()

        shift = Shift.objects.create(
            order_round=self.order_round,
            start=time(14, 0),
            end=time(16, 0)
        )
        self.assertEqual(shift.distribution_coordinator, coordinator)

    def test_transport_coordinator_property(self):
        """Test transport_coordinator returns from order_round."""
        coordinator = VokoUserFactory.create()
        self.order_round.transport_coordinator = coordinator
        self.order_round.save()

        shift = Shift.objects.create(
            order_round=self.order_round,
            start=time(14, 0),
            end=time(16, 0)
        )
        self.assertEqual(shift.transport_coordinator, coordinator)

    def test_members_names_property(self):
        """Test members_names returns list of member names."""
        member1 = VokoUserFactory.create(first_name="Jan", last_name="Janssen")
        member2 = VokoUserFactory.create(first_name="Piet", last_name="Pietersen")

        shift = Shift.objects.create(
            order_round=self.order_round,
            start=time(14, 0),
            end=time(16, 0)
        )
        shift.members.add(member1, member2)

        names = shift.members_names
        self.assertIn("Jan Janssen", names)
        self.assertIn("Piet Pietersen", names)
        self.assertEqual(len(names), 2)

    def test_members_names_empty(self):
        """Test members_names with no members."""
        shift = Shift.objects.create(
            order_round=self.order_round,
            start=time(14, 0),
            end=time(16, 0)
        )
        self.assertEqual(shift.members_names, [])

    def test_as_event_returns_transient_event(self):
        """Test as_event returns a TransientEvent."""
        shift = Shift.objects.create(
            order_round=self.order_round,
            start=time(14, 0),
            end=time(16, 0)
        )
        event = shift.as_event()

        self.assertEqual(event.address, self.pickup_location.address)
        self.assertIn("Uitdeeldienst", event.title)
        self.assertEqual(event.date, self.order_round.collect_datetime.date())
        self.assertEqual(event.time, time(14, 0))
        self.assertTrue(event.is_shift)

    def test_key_collectors_returns_none_without_next_round(self):
        """Test key_collectors returns None when no next round."""
        shift = Shift.objects.create(
            order_round=self.order_round,
            start=time(14, 0),
            end=time(16, 0)
        )
        self.assertIsNone(shift.key_collectors)

    def test_ordering_by_start_time(self):
        """Test shifts are ordered by start time."""
        shift1 = Shift.objects.create(
            order_round=self.order_round,
            start=time(16, 0),
            end=time(18, 0)
        )
        shift2 = Shift.objects.create(
            order_round=self.order_round,
            start=time(14, 0),
            end=time(16, 0)
        )

        shifts = list(Shift.objects.all())
        # shift2 should come first due to earlier start time
        self.assertEqual(shifts[0], shift2)
        self.assertEqual(shifts[1], shift1)
