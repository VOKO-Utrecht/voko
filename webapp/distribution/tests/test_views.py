# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, time
from unittest import mock

import pytz
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import Group

from distribution.models import Shift
from ordering.models import OrderRound, PickupLocation
from accounts.tests.factories import VokoUserFactory, AddressFactory
from vokou.testing import VokoTestCase, suppressWarnings


class ScheduleViewTest(VokoTestCase):
    """Tests for the Schedule view."""

    def setUp(self):
        """Set up test data."""
        self.now = datetime.now(pytz.utc)
        self.address = AddressFactory.create()
        self.pickup_location = PickupLocation.objects.create(
            name="Test Location",
            address=self.address
        )

    def _create_order_round(self, days_offset=1):
        """Create an order round."""
        return OrderRound.objects.create(
            open_for_orders=self.now - timedelta(days=2),
            closed_for_orders=self.now - timedelta(days=1),
            collect_datetime=self.now + timedelta(days=days_offset),
            pickup_location=self.pickup_location
        )

    def _create_shift(self, order_round, start=time(14, 0), end=time(16, 0)):
        """Create a shift."""
        return Shift.objects.create(
            order_round=order_round,
            start=start,
            end=end
        )

    def test_schedule_requires_login(self):
        """Test schedule page requires login."""
        response = self.client.get(reverse("distribution_schedule"))
        self.assertEqual(response.status_code, 302)

    def test_schedule_page_renders(self):
        """Test schedule page renders for logged in user."""
        self.login()
        response = self.client.get(reverse("distribution_schedule"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "distribution/schedule.html")

    def test_schedule_shows_user_shifts(self):
        """Test schedule shows shifts where user is member."""
        self.login()
        order_round = self._create_order_round()
        shift = self._create_shift(order_round)
        shift.members.add(self.user)

        response = self.client.get(reverse("distribution_schedule"))
        self.assertIn(shift, response.context["object_list"])

    def test_schedule_hides_other_user_shifts(self):
        """Test regular user doesn't see other user's shifts."""
        self.login()
        order_round = self._create_order_round()
        shift = self._create_shift(order_round)
        other_user = VokoUserFactory.create()
        shift.members.add(other_user)

        response = self.client.get(reverse("distribution_schedule"))
        self.assertNotIn(shift, response.context["object_list"])

    def test_schedule_coordinator_sees_all_shifts(self):
        """Test Uitdeelcoordinatoren sees all shifts."""
        self.login(group="Uitdeelcoordinatoren")
        order_round = self._create_order_round()
        shift = self._create_shift(order_round)
        other_user = VokoUserFactory.create()
        shift.members.add(other_user)

        response = self.client.get(reverse("distribution_schedule"))
        self.assertIn(shift, response.context["object_list"])

    def test_schedule_context_iscoordinator_false(self):
        """Test isCoordinator is False for regular user."""
        self.login()
        response = self.client.get(reverse("distribution_schedule"))
        self.assertFalse(response.context["isCoordinator"])

    def test_schedule_context_iscoordinator_true(self):
        """Test isCoordinator is True for coordinator."""
        self.login(group="Uitdeelcoordinatoren")
        response = self.client.get(reverse("distribution_schedule"))
        self.assertTrue(response.context["isCoordinator"])

    def test_schedule_hides_past_shifts(self):
        """Test schedule doesn't show past shifts."""
        self.login()
        # Create a past order round
        order_round = self._create_order_round(days_offset=-10)
        shift = self._create_shift(order_round)
        shift.members.add(self.user)

        response = self.client.get(reverse("distribution_schedule"))
        self.assertNotIn(shift, response.context["object_list"])


class ShiftViewTest(VokoTestCase):
    """Tests for the Shift detail view."""

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

    def _create_shift(self, start=time(14, 0), end=time(16, 0)):
        """Create a shift."""
        return Shift.objects.create(
            order_round=self.order_round,
            start=start,
            end=end
        )

    def test_shift_requires_login(self):
        """Test shift page requires login."""
        shift = self._create_shift()
        response = self.client.get(reverse("shift", kwargs={"slug": shift.slug}))
        self.assertEqual(response.status_code, 302)

    def test_shift_member_can_view(self):
        """Test shift member can view shift."""
        self.login()
        shift = self._create_shift()
        shift.members.add(self.user)

        response = self.client.get(reverse("shift", kwargs={"slug": shift.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "distribution/shift.html")

    def test_shift_coordinator_can_view(self):
        """Test Uitdeelcoordinatoren can view any shift."""
        self.login(group="Uitdeelcoordinatoren")
        shift = self._create_shift()
        other_user = VokoUserFactory.create()
        shift.members.add(other_user)

        response = self.client.get(reverse("shift", kwargs={"slug": shift.slug}))
        self.assertEqual(response.status_code, 200)

    @suppressWarnings
    def test_shift_unauthorized_user_denied(self):
        """Test unauthorized user cannot view shift."""
        self.login()
        shift = self._create_shift()
        other_user = VokoUserFactory.create()
        shift.members.add(other_user)

        response = self.client.get(reverse("shift", kwargs={"slug": shift.slug}))
        self.assertEqual(response.status_code, 403)


class MembersViewTest(VokoTestCase):
    """Tests for the Members view."""

    def test_members_requires_login(self):
        """Test members page requires login."""
        response = self.client.get(reverse("distribution_members"))
        self.assertEqual(response.status_code, 302)

    @suppressWarnings
    def test_members_requires_distribution_group(self):
        """Test members page requires proper group."""
        self.login()
        response = self.client.get(reverse("distribution_members"))
        # GroupRequiredMixin redirects unauthorized users
        self.assertIn(response.status_code, [302, 403])

    def test_members_coordinator_can_view(self):
        """Test Uitdeelcoordinatoren can view members."""
        self.login(group="Uitdeelcoordinatoren")
        response = self.client.get(reverse("distribution_members"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "distribution/members.html")

    def test_members_uitdeel_group_can_view(self):
        """Test Uitdeel group can view members."""
        self.login(group="Uitdeel")
        response = self.client.get(reverse("distribution_members"))
        self.assertEqual(response.status_code, 200)

    def test_members_admin_can_view(self):
        """Test Admin group can view members."""
        self.login(group="Admin")
        response = self.client.get(reverse("distribution_members"))
        self.assertEqual(response.status_code, 200)
