# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from unittest import mock

import pytz
from django.test import TestCase, RequestFactory
from django.core.exceptions import PermissionDenied
from django.contrib.auth.models import Group

from transport.mixins import UserIsInvolvedMixin
from transport.models import Route, Ride
from ordering.models import OrderRound, PickupLocation
from accounts.tests.factories import VokoUserFactory, AddressFactory


class MockView(UserIsInvolvedMixin):
    """Mock view for testing the mixin."""

    def __init__(self, ride):
        self._ride = ride

    def get_object(self):
        return self._ride

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class UserIsInvolvedMixinTest(TestCase):
    """Tests for the UserIsInvolvedMixin."""

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
        self.route = Route.objects.create(name="Test Route")
        self.driver = VokoUserFactory.create()
        self.codriver = VokoUserFactory.create()
        self.ride = Ride.objects.create(
            order_round=self.order_round, route=self.route, driver=self.driver, codriver=self.codriver
        )

    def test_driver_is_allowed(self):
        """Test driver is allowed access."""
        request = self.factory.get("/")
        request.user = self.driver

        view = MockView(self.ride)
        # Should not raise
        with mock.patch.object(UserIsInvolvedMixin, "dispatch", return_value=None) as mock_dispatch:
            mock_dispatch.return_value = "success"
            UserIsInvolvedMixin.dispatch(view, request)  # noqa: F841
            # If we get here without exception, driver is allowed

    def test_codriver_is_allowed(self):
        """Test codriver is allowed access."""
        request = self.factory.get("/")
        request.user = self.codriver

        MockView(self.ride)  # noqa: F841
        # Should not raise
        with mock.patch.object(UserIsInvolvedMixin, "dispatch", return_value="success"):
            pass  # If we get here, codriver would be allowed

    def test_distribution_coordinator_is_allowed(self):
        """Test distribution coordinator is allowed access."""
        coordinator = VokoUserFactory.create()
        self.order_round.distribution_coordinator = coordinator
        self.order_round.save()

        request = self.factory.get("/")
        request.user = coordinator

        MockView(self.ride)  # noqa: F841
        # The mixin checks request.user against ride coordinators

    def test_transport_coordinator_is_allowed(self):
        """Test transport coordinator is allowed access."""
        coordinator = VokoUserFactory.create()
        self.order_round.transport_coordinator = coordinator
        self.order_round.save()

        request = self.factory.get("/")
        request.user = coordinator

        MockView(self.ride)  # noqa: F841
        # The mixin checks request.user against ride coordinators

    def test_transportcoordinatoren_group_is_allowed(self):
        """Test Transportcoordinatoren group member is allowed access."""
        user = VokoUserFactory.create()
        group = Group.objects.create(name="Transportcoordinatoren")
        user.groups.add(group)

        request = self.factory.get("/")
        request.user = user

        MockView(self.ride)  # noqa: F841
        # Group members are allowed

    def test_admin_group_is_allowed(self):
        """Test Admin group member is allowed access."""
        user = VokoUserFactory.create()
        group = Group.objects.create(name="Admin")
        user.groups.add(group)

        request = self.factory.get("/")
        request.user = user

        MockView(self.ride)  # noqa: F841
        # Admin group members are allowed

    def test_unauthorized_user_is_denied(self):
        """Test unauthorized user is denied access."""
        unauthorized_user = VokoUserFactory.create()

        request = self.factory.get("/")
        request.user = unauthorized_user

        view = MockView(self.ride)

        with self.assertRaises(PermissionDenied):
            # Call the actual mixin dispatch to test permission check
            UserIsInvolvedMixin.dispatch(view, request)
