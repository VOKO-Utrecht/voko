# -*- coding: utf-8 -*-
from datetime import datetime, timedelta, time
from unittest import mock

import pytz
from django.test import TestCase, RequestFactory
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Group

from distribution.mixins import UserIsInvolvedWithShiftMixin
from distribution.models import Shift
from ordering.models import OrderRound, PickupLocation
from accounts.tests.factories import VokoUserFactory, AddressFactory


class MockView(UserIsInvolvedWithShiftMixin):
    """Mock view for testing the mixin."""

    def __init__(self, shift):
        self._shift = shift

    def get_object(self):
        return self._shift

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class UserIsInvolvedWithShiftMixinTest(TestCase):
    """Tests for the UserIsInvolvedWithShiftMixin."""

    def setUp(self):
        """Set up test data."""
        self.factory = RequestFactory()
        self.now = datetime.now(pytz.utc)
        self.address = AddressFactory.create()
        self.pickup_location = PickupLocation.objects.create(name="Test Location", address=self.address)
        self.order_round = OrderRound.objects.create(
            open_for_orders=self.now - timedelta(days=2),
            closed_for_orders=self.now - timedelta(days=1),
            collect_datetime=self.now + timedelta(days=1),
            pickup_location=self.pickup_location,
        )
        self.shift = Shift.objects.create(order_round=self.order_round, start=time(14, 0), end=time(16, 0))
        self.member = VokoUserFactory.create()
        self.shift.members.add(self.member)

    def test_member_is_allowed(self):
        """Test shift member is allowed access."""
        request = self.factory.get("/")
        request.user = self.member

        MockView(self.shift)  # noqa: F841
        # Should not raise - member is in shift.members
        with mock.patch.object(UserIsInvolvedWithShiftMixin, "dispatch", return_value="success"):
            pass

    def test_uitdeelcoordinatoren_group_is_allowed(self):
        """Test Uitdeelcoordinatoren group member is allowed access."""
        user = VokoUserFactory.create()
        group = Group.objects.create(name="Uitdeelcoordinatoren")
        user.groups.add(group)

        request = self.factory.get("/")
        request.user = user

        MockView(self.shift)  # noqa: F841
        # Group members are allowed

    def test_unauthorized_user_is_denied(self):
        """Test unauthorized user is denied access."""
        unauthorized_user = VokoUserFactory.create()

        request = self.factory.get("/")
        request.user = unauthorized_user

        view = MockView(self.shift)

        with self.assertRaises(PermissionDenied):
            UserIsInvolvedWithShiftMixin.dispatch(view, request)

    def test_non_member_without_group_is_denied(self):
        """Test non-member without coordinator group is denied."""
        non_member = VokoUserFactory.create()
        # Add to a different group
        other_group = Group.objects.create(name="OtherGroup")
        non_member.groups.add(other_group)

        request = self.factory.get("/")
        request.user = non_member

        view = MockView(self.shift)

        with self.assertRaises(PermissionDenied):
            UserIsInvolvedWithShiftMixin.dispatch(view, request)
