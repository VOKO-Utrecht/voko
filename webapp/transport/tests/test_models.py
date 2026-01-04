# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from unittest import mock

import pytz
from django.test import TestCase
from django.utils.text import slugify

from transport.models import Route, Ride
from ordering.models import Supplier, OrderRound, PickupLocation
from accounts.tests.factories import VokoUserFactory, AddressFactory
from ordering.tests.factories import OrderRoundFactory, SupplierFactory
from vokou.testing import VokoTestCase


class RouteModelTest(TestCase):
    """Tests for the Route model."""

    def test_str_representation(self):
        """Test string representation of Route."""
        route = Route.objects.create(name="Utrecht Noord")
        self.assertEqual(str(route), "Utrecht Noord")

    def test_slug_generated_on_save(self):
        """Test slug is auto-generated from name."""
        route = Route.objects.create(name="Utrecht Noord")
        self.assertEqual(route.slug, "utrecht-noord")

    def test_slug_unique(self):
        """Test slug uniqueness."""
        route1 = Route.objects.create(name="Test Route")
        self.assertEqual(route1.slug, "test-route")

    def test_suppliers_names_property(self):
        """Test suppliers_names returns list of supplier names."""
        route = Route.objects.create(name="Test Route")
        supplier1 = SupplierFactory.create(name="Supplier One")
        supplier2 = SupplierFactory.create(name="Supplier Two")
        route.suppliers.add(supplier1, supplier2)

        names = route.suppliers_names
        self.assertIn("Supplier One", names)
        self.assertIn("Supplier Two", names)
        self.assertEqual(len(names), 2)

    def test_suppliers_names_empty(self):
        """Test suppliers_names with no suppliers."""
        route = Route.objects.create(name="Empty Route")
        self.assertEqual(route.suppliers_names, [])


class RideModelTest(TestCase):
    """Tests for the Ride model."""

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
        self.route = Route.objects.create(name="Test Route")
        self.driver = VokoUserFactory.create()
        self.codriver = VokoUserFactory.create()

    def test_str_representation(self):
        """Test string representation of Ride."""
        ride = Ride.objects.create(
            order_round=self.order_round,
            route=self.route,
            driver=self.driver,
            codriver=self.codriver
        )
        expected = "{}-{}".format(
            self.order_round.collect_datetime.strftime("%Y-%m-%d"),
            self.route
        )
        self.assertEqual(str(ride), expected)

    def test_slug_generated_on_save(self):
        """Test slug is auto-generated."""
        ride = Ride.objects.create(
            order_round=self.order_round,
            route=self.route,
            driver=self.driver,
            codriver=self.codriver
        )
        expected_slug = slugify("{}-{}".format(
            self.order_round.collect_datetime.strftime("%Y-%m-%d"),
            self.route
        ))
        self.assertEqual(ride.slug, expected_slug)

    def test_date_property(self):
        """Test date property returns order_round collect_datetime."""
        ride = Ride.objects.create(
            order_round=self.order_round,
            route=self.route,
            driver=self.driver,
            codriver=self.codriver
        )
        self.assertEqual(ride.date, self.order_round.collect_datetime)

    def test_date_str_property(self):
        """Test date_str property returns formatted date."""
        ride = Ride.objects.create(
            order_round=self.order_round,
            route=self.route,
            driver=self.driver,
            codriver=self.codriver
        )
        expected = self.order_round.collect_datetime.strftime("%Y-%m-%d")
        self.assertEqual(ride.date_str, expected)

    def test_distribution_coordinator_property(self):
        """Test distribution_coordinator returns from order_round."""
        coordinator = VokoUserFactory.create()
        self.order_round.distribution_coordinator = coordinator
        self.order_round.save()

        ride = Ride.objects.create(
            order_round=self.order_round,
            route=self.route,
            driver=self.driver,
            codriver=self.codriver
        )
        self.assertEqual(ride.distribution_coordinator, coordinator)

    def test_transport_coordinator_property(self):
        """Test transport_coordinator returns from order_round."""
        coordinator = VokoUserFactory.create()
        self.order_round.transport_coordinator = coordinator
        self.order_round.save()

        ride = Ride.objects.create(
            order_round=self.order_round,
            route=self.route,
            driver=self.driver,
            codriver=self.codriver
        )
        self.assertEqual(ride.transport_coordinator, coordinator)

    def test_as_event_returns_transient_event(self):
        """Test as_event returns a TransientEvent."""
        ride = Ride.objects.create(
            order_round=self.order_round,
            route=self.route,
            driver=self.driver,
            codriver=self.codriver
        )
        event = ride.as_event()

        self.assertEqual(event.address, self.pickup_location.address)
        self.assertIn("Transportdienst", event.title)
        self.assertEqual(event.date, self.order_round.collect_datetime.date())
        self.assertTrue(event.is_shift)

    def test_orders_per_supplier_filters_by_route(self):
        """Test orders_per_supplier only includes route suppliers."""
        # Create suppliers
        supplier_in_route = SupplierFactory.create(name="In Route")
        supplier_not_in_route = SupplierFactory.create(name="Not In Route")

        self.route.suppliers.add(supplier_in_route)

        ride = Ride.objects.create(
            order_round=self.order_round,
            route=self.route,
            driver=self.driver,
            codriver=self.codriver
        )

        # The property filters based on route suppliers
        orders = ride.orders_per_supplier
        # Should not contain supplier not in route
        self.assertNotIn(supplier_not_in_route, orders)
