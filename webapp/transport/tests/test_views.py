# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

import pytz
from django.urls import reverse

from transport.models import Route, Ride
from ordering.models import OrderRound, PickupLocation
from accounts.models import UserProfile
from accounts.tests.factories import VokoUserFactory, AddressFactory
from vokou.testing import VokoTestCase, suppressWarnings


class ScheduleViewTest(VokoTestCase):
    """Tests for the Schedule view."""

    def setUp(self):
        """Set up test data."""
        self.now = datetime.now(pytz.utc)
        self.address = AddressFactory.create()
        self.pickup_location = PickupLocation.objects.create(name="Test Location", address=self.address)

    def _create_order_round(self, days_offset=1):
        """Create an order round."""
        return OrderRound.objects.create(
            open_for_orders=self.now - timedelta(days=2),
            closed_for_orders=self.now - timedelta(days=1),
            collect_datetime=self.now + timedelta(days=days_offset),
            pickup_location=self.pickup_location,
        )

    def _create_ride(self, order_round, driver, codriver):
        """Create a ride."""
        route = Route.objects.create(name="Test Route {}".format(order_round.id))
        return Ride.objects.create(order_round=order_round, route=route, driver=driver, codriver=codriver)

    def test_schedule_requires_login(self):
        """Test schedule page requires login."""
        response = self.client.get(reverse("schedule"))
        self.assertEqual(response.status_code, 302)

    def test_schedule_page_renders(self):
        """Test schedule page renders for logged in user."""
        self.login()
        response = self.client.get(reverse("schedule"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transport/schedule.html")

    def test_schedule_shows_user_rides_as_driver(self):
        """Test schedule shows rides where user is driver."""
        self.login()
        order_round = self._create_order_round()
        other_user = VokoUserFactory.create()
        ride = self._create_ride(order_round, self.user, other_user)

        response = self.client.get(reverse("schedule"))
        self.assertIn(ride, response.context["object_list"])

    def test_schedule_shows_user_rides_as_codriver(self):
        """Test schedule shows rides where user is codriver."""
        self.login()
        order_round = self._create_order_round()
        other_user = VokoUserFactory.create()
        ride = self._create_ride(order_round, other_user, self.user)

        response = self.client.get(reverse("schedule"))
        self.assertIn(ride, response.context["object_list"])

    def test_schedule_shows_coordinator_rides(self):
        """Test schedule shows rides where user is transport coordinator."""
        self.login()
        order_round = self._create_order_round()
        order_round.transport_coordinator = self.user
        order_round.save()

        other_user1 = VokoUserFactory.create()
        other_user2 = VokoUserFactory.create()
        ride = self._create_ride(order_round, other_user1, other_user2)

        response = self.client.get(reverse("schedule"))
        self.assertIn(ride, response.context["object_list"])

    def test_schedule_coordinator_sees_all_rides(self):
        """Test Transportcoordinatoren group sees all rides."""
        self.login(group="Transportcoordinatoren")
        order_round = self._create_order_round()

        other_user1 = VokoUserFactory.create()
        other_user2 = VokoUserFactory.create()
        ride = self._create_ride(order_round, other_user1, other_user2)

        response = self.client.get(reverse("schedule"))
        self.assertIn(ride, response.context["object_list"])

    def test_schedule_admin_sees_all_rides(self):
        """Test Admin group sees all rides including past."""
        self.login(group="Admin")
        # Create a past ride
        order_round = self._create_order_round(days_offset=-10)
        other_user1 = VokoUserFactory.create()
        other_user2 = VokoUserFactory.create()
        ride = self._create_ride(order_round, other_user1, other_user2)

        response = self.client.get(reverse("schedule"))
        self.assertIn(ride, response.context["object_list"])

    def test_schedule_regular_user_no_past_rides(self):
        """Test regular user doesn't see past rides."""
        self.login()
        # Create a past ride where user is driver
        order_round = self._create_order_round(days_offset=-10)
        other_user = VokoUserFactory.create()
        ride = self._create_ride(order_round, self.user, other_user)

        response = self.client.get(reverse("schedule"))
        self.assertNotIn(ride, response.context["object_list"])


class RideViewTest(VokoTestCase):
    """Tests for the Ride detail view."""

    def setUp(self):
        """Set up test data."""
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

    def _create_ride(self, driver, codriver):
        """Create a ride."""
        return Ride.objects.create(order_round=self.order_round, route=self.route, driver=driver, codriver=codriver)

    def test_ride_requires_login(self):
        """Test ride page requires login."""
        driver = VokoUserFactory.create()
        codriver = VokoUserFactory.create()
        ride = self._create_ride(driver, codriver)

        response = self.client.get(reverse("ride", kwargs={"slug": ride.slug}))
        self.assertEqual(response.status_code, 302)

    def test_ride_driver_can_view(self):
        """Test driver can view ride."""
        self.login()
        codriver = VokoUserFactory.create()
        ride = self._create_ride(self.user, codriver)

        response = self.client.get(reverse("ride", kwargs={"slug": ride.slug}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transport/ride.html")

    def test_ride_codriver_can_view(self):
        """Test codriver can view ride."""
        self.login()
        driver = VokoUserFactory.create()
        ride = self._create_ride(driver, self.user)

        response = self.client.get(reverse("ride", kwargs={"slug": ride.slug}))
        self.assertEqual(response.status_code, 200)

    def test_ride_distribution_coordinator_can_view(self):
        """Test distribution coordinator can view ride."""
        self.login()
        self.order_round.distribution_coordinator = self.user
        self.order_round.save()

        driver = VokoUserFactory.create()
        codriver = VokoUserFactory.create()
        ride = self._create_ride(driver, codriver)

        response = self.client.get(reverse("ride", kwargs={"slug": ride.slug}))
        self.assertEqual(response.status_code, 200)

    def test_ride_transport_coordinator_can_view(self):
        """Test transport coordinator can view ride."""
        self.login()
        self.order_round.transport_coordinator = self.user
        self.order_round.save()

        driver = VokoUserFactory.create()
        codriver = VokoUserFactory.create()
        ride = self._create_ride(driver, codriver)

        response = self.client.get(reverse("ride", kwargs={"slug": ride.slug}))
        self.assertEqual(response.status_code, 200)

    def test_ride_coordinator_group_can_view(self):
        """Test Transportcoordinatoren group can view any ride."""
        self.login(group="Transportcoordinatoren")

        driver = VokoUserFactory.create()
        codriver = VokoUserFactory.create()
        ride = self._create_ride(driver, codriver)

        response = self.client.get(reverse("ride", kwargs={"slug": ride.slug}))
        self.assertEqual(response.status_code, 200)

    @suppressWarnings
    def test_ride_unauthorized_user_denied(self):
        """Test unauthorized user cannot view ride."""
        self.login()

        driver = VokoUserFactory.create()
        codriver = VokoUserFactory.create()
        ride = self._create_ride(driver, codriver)

        response = self.client.get(reverse("ride", kwargs={"slug": ride.slug}))
        self.assertEqual(response.status_code, 403)


class CarsViewTest(VokoTestCase):
    """Tests for the Cars view."""

    def test_cars_requires_login(self):
        """Test cars page requires login."""
        response = self.client.get(reverse("cars"))
        self.assertEqual(response.status_code, 302)

    @suppressWarnings
    def test_cars_requires_transport_group(self):
        """Test cars page requires Transport group."""
        self.login()
        response = self.client.get(reverse("cars"))
        # GroupRequiredMixin redirects unauthorized users
        self.assertIn(response.status_code, [302, 403])

    def test_cars_transport_group_can_view(self):
        """Test Transport group can view cars."""
        self.login(group="Transport")
        response = self.client.get(reverse("cars"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transport/cars.html")

    def test_cars_admin_group_can_view(self):
        """Test Admin group can view cars."""
        self.login(group="Admin")
        response = self.client.get(reverse("cars"))
        self.assertEqual(response.status_code, 200)

    def test_cars_shows_users_sharing_cars(self):
        """Test cars page shows users who share cars."""
        self.login(group="Transport")

        # Create user with car
        user_with_car = VokoUserFactory.create()
        UserProfile.objects.create(user=user_with_car, shares_car=True, car_neighborhood="Centrum", car_type="Station")

        # Create user without car
        user_without_car = VokoUserFactory.create()
        UserProfile.objects.create(user=user_without_car, shares_car=False)

        response = self.client.get(reverse("cars"))
        self.assertIn(user_with_car, response.context["object_list"])
        self.assertNotIn(user_without_car, response.context["object_list"])


class MembersViewTest(VokoTestCase):
    """Tests for the Members view."""

    def test_members_requires_login(self):
        """Test members page requires login."""
        response = self.client.get(reverse("transport_members"))
        self.assertEqual(response.status_code, 302)

    @suppressWarnings
    def test_members_requires_transport_group(self):
        """Test members page requires Transport group."""
        self.login()
        response = self.client.get(reverse("transport_members"))
        # GroupRequiredMixin redirects unauthorized users
        self.assertIn(response.status_code, [302, 403])

    def test_members_transport_group_can_view(self):
        """Test Transport group can view members."""
        self.login(group="Transport")
        response = self.client.get(reverse("transport_members"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "transport/members.html")
