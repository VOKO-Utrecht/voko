# -*- coding: utf-8 -*-
from django.test import TestCase

from accounts.tests.factories import VokoUserFactory
from log.models import EventLog


class EventLogModelTest(TestCase):
    """Tests for the EventLog model."""

    def test_str_representation(self):
        """Test string representation of EventLog."""
        log = EventLog.objects.create(event="User logged in")
        self.assertEqual(str(log), "User logged in")

    def test_event_field_required(self):
        """Test event field stores event description."""
        log = EventLog.objects.create(event="Test event occurred")
        self.assertEqual(log.event, "Test event occurred")

    def test_operator_field(self):
        """Test operator field stores the user who performed action."""
        operator = VokoUserFactory.create()
        log = EventLog.objects.create(
            event="Admin action",
            operator=operator
        )
        self.assertEqual(log.operator, operator)

    def test_operator_can_be_null(self):
        """Test operator can be null (for system events)."""
        log = EventLog.objects.create(event="System event")
        self.assertIsNone(log.operator)

    def test_user_field(self):
        """Test user field stores the user affected by action."""
        user = VokoUserFactory.create()
        log = EventLog.objects.create(
            event="User action",
            user=user
        )
        self.assertEqual(log.user, user)

    def test_user_can_be_null(self):
        """Test user can be null."""
        log = EventLog.objects.create(event="Global event")
        self.assertIsNone(log.user)

    def test_extra_field(self):
        """Test extra field stores additional data."""
        log = EventLog.objects.create(
            event="Complex event",
            extra="{'detail': 'additional info', 'count': 42}"
        )
        self.assertEqual(log.extra, "{'detail': 'additional info', 'count': 42}")

    def test_extra_can_be_null(self):
        """Test extra can be null."""
        log = EventLog.objects.create(event="Simple event")
        self.assertIsNone(log.extra)

    def test_extra_can_be_blank(self):
        """Test extra can be blank."""
        log = EventLog.objects.create(event="Simple event", extra="")
        self.assertEqual(log.extra, "")

    def test_timestamps_are_set(self):
        """Test created and modified timestamps are set."""
        log = EventLog.objects.create(event="Test")
        self.assertIsNotNone(log.created)
        self.assertIsNotNone(log.modified)

    def test_full_log_entry(self):
        """Test creating a full log entry with all fields."""
        operator = VokoUserFactory.create()
        user = VokoUserFactory.create()

        log = EventLog.objects.create(
            operator=operator,
            user=user,
            event="User profile updated by admin",
            extra="Changed: first_name, last_name"
        )

        self.assertEqual(log.operator, operator)
        self.assertEqual(log.user, user)
        self.assertEqual(log.event, "User profile updated by admin")
        self.assertEqual(log.extra, "Changed: first_name, last_name")

    def test_operator_logs_related_name(self):
        """Test operator can access their logs via related name."""
        operator = VokoUserFactory.create()
        log = EventLog.objects.create(
            operator=operator,
            event="Admin action"
        )

        self.assertIn(log, operator.operator_logs.all())

    def test_user_logs_related_name(self):
        """Test user can access logs about them via related name."""
        user = VokoUserFactory.create()
        log = EventLog.objects.create(
            user=user,
            event="User event"
        )

        self.assertIn(log, user.user_logs.all())

    def test_deleting_operator_sets_null(self):
        """Test deleting operator sets log.operator to null."""
        operator = VokoUserFactory.create()
        log = EventLog.objects.create(
            operator=operator,
            event="Admin action"
        )
        operator_id = operator.pk

        operator.delete()
        log.refresh_from_db()

        self.assertIsNone(log.operator)

    def test_deleting_user_sets_null(self):
        """Test deleting user sets log.user to null."""
        user = VokoUserFactory.create()
        log = EventLog.objects.create(
            user=user,
            event="User event"
        )

        user.delete()
        log.refresh_from_db()

        self.assertIsNone(log.user)
