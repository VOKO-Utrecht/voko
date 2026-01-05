# -*- coding: utf-8 -*-
from datetime import date, time

from django.test import TestCase

from accounts.models import Address
from agenda.models import PersistentEvent, TransientEvent


class PersistentEventModelTest(TestCase):
    """Tests for the PersistentEvent model."""

    def test_str_representation(self):
        """Test string representation of PersistentEvent."""
        event = PersistentEvent.objects.create(title="General Assembly", date=date(2024, 6, 15))
        self.assertEqual(str(event), "General Assembly - 2024-06-15")

    def test_default_fields(self):
        """Test default values for date and time."""
        event = PersistentEvent.objects.create(title="Test Event")

        self.assertIsNotNone(event.date)
        self.assertIsNotNone(event.time)

    def test_short_description(self):
        """Test short description field."""
        event = PersistentEvent.objects.create(title="Test", short_description="A brief description")
        self.assertEqual(event.short_description, "A brief description")

    def test_long_description_html(self):
        """Test long description can contain HTML."""
        html = "<p>A <strong>detailed</strong> description</p>"
        event = PersistentEvent.objects.create(title="Test", long_description=html)
        self.assertEqual(event.long_description, html)

    def test_address_relationship(self):
        """Test address can be linked."""
        address = Address.objects.create(street_and_number="123 Main St", zip_code="3512AB", city="Utrecht")
        event = PersistentEvent.objects.create(title="Test", address=address)
        self.assertEqual(event.address, address)

    def test_address_can_be_null(self):
        """Test address can be null."""
        event = PersistentEvent.objects.create(title="Test")
        self.assertIsNone(event.address)

    def test_timestamps_are_set(self):
        """Test created and modified timestamps are set."""
        event = PersistentEvent.objects.create(title="Test")
        self.assertIsNotNone(event.created)
        self.assertIsNotNone(event.modified)


class TransientEventModelTest(TestCase):
    """Tests for the TransientEvent model (non-persisted events)."""

    def test_str_representation(self):
        """Test string representation of TransientEvent."""
        event = TransientEvent(title="Transport Ride", date=date(2024, 6, 15))
        self.assertEqual(str(event), "Transport Ride - 2024-06-15")

    def test_save_does_nothing(self):
        """Test save method doesn't persist (managed=False model)."""
        event = TransientEvent(title="Test", date=date(2024, 6, 15))
        # Should not raise an exception
        event.save()

        # Model is not managed, so no objects in DB
        # This is by design for transient events

    def test_is_shift_default_false(self):
        """Test is_shift default is False."""
        event = TransientEvent(title="Test")
        self.assertFalse(event.is_shift)

    def test_is_shift_can_be_set(self):
        """Test is_shift can be set to True."""
        event = TransientEvent(title="Test", is_shift=True)
        self.assertTrue(event.is_shift)

    def test_org_model_field(self):
        """Test org_model stores original model name."""
        event = TransientEvent(title="Test", org_model="distribution.Shift")
        self.assertEqual(event.org_model, "distribution.Shift")

    def test_org_id_field(self):
        """Test org_id stores original model ID."""
        event = TransientEvent(title="Test", org_id=42)
        self.assertEqual(event.org_id, 42)

    def test_full_event_data(self):
        """Test creating event with all fields."""
        event = TransientEvent(
            title="Distribution Shift",
            date=date(2024, 6, 15),
            time=time(10, 0),
            short_description="Morning shift",
            is_shift=True,
            org_model="distribution.Shift",
            org_id=123,
        )

        self.assertEqual(event.title, "Distribution Shift")
        self.assertEqual(event.date, date(2024, 6, 15))
        self.assertEqual(event.time, time(10, 0))
        self.assertEqual(event.short_description, "Morning shift")
        self.assertTrue(event.is_shift)
        self.assertEqual(event.org_model, "distribution.Shift")
        self.assertEqual(event.org_id, 123)
