# -*- coding: utf-8 -*-
import json
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import Group
from django.utils import timezone

from vokou.testing import VokoTestCase
from ordering.models import OrderRound


class OrdersAPIViewTest(VokoTestCase):
    """Tests for the Orders API views."""

    def setUp(self):
        super().setUp()
        # Create required groups
        self.it_group, _ = Group.objects.get_or_create(name="IT")
        self.promo_group, _ = Group.objects.get_or_create(name="Promo")

    def _create_order_round(self):
        """Create a test order round."""
        now = timezone.now()
        return OrderRound.objects.create(
            open_for_orders=now - timedelta(days=7),
            closed_for_orders=now - timedelta(days=1),
            collect_datetime=now + timedelta(days=1),
            markup_percentage=Decimal("7.5"),
        )

    def test_orders_json_requires_login(self):
        """Test JSON view requires login."""
        response = self.client.get("/api/orders.json")
        self.assertEqual(response.status_code, 302)

    def test_orders_csv_requires_login(self):
        """Test CSV view requires login."""
        response = self.client.get("/api/orders.csv")
        self.assertEqual(response.status_code, 302)

    def test_orders_json_requires_group(self):
        """Test JSON view requires IT or Promo group."""
        self.login()
        response = self.client.get("/api/orders.json")
        # GroupRequiredMixin redirects or returns 403
        self.assertIn(response.status_code, [302, 403])

    def test_orders_csv_requires_group(self):
        """Test CSV view requires IT or Promo group."""
        self.login()
        response = self.client.get("/api/orders.csv")
        self.assertIn(response.status_code, [302, 403])

    def test_orders_json_accessible_for_it_group(self):
        """Test JSON view accessible for IT group member."""
        self.login()
        self.user.groups.add(self.it_group)

        response = self.client.get("/api/orders.json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_orders_csv_accessible_for_it_group(self):
        """Test CSV view accessible for IT group member."""
        self.login()
        self.user.groups.add(self.it_group)
        self._create_order_round()  # Need data for CSV

        response = self.client.get("/api/orders.csv")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")

    def test_orders_json_accessible_for_promo_group(self):
        """Test JSON view accessible for Promo group member."""
        self.login()
        self.user.groups.add(self.promo_group)

        response = self.client.get("/api/orders.json")
        self.assertEqual(response.status_code, 200)

    def test_orders_json_returns_data(self):
        """Test JSON view returns order round data."""
        self.login()
        self.user.groups.add(self.it_group)
        self._create_order_round()

        response = self.client.get("/api/orders.json")
        data = json.loads(response.content)

        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertIn("number_of_orders", data[0])
        self.assertIn("total_revenue", data[0])
        self.assertIn("markup_percentage", data[0])


class AccountsAPIViewTest(VokoTestCase):
    """Tests for the Accounts API views."""

    def setUp(self):
        super().setUp()
        self.it_group, _ = Group.objects.get_or_create(name="IT")
        self.promo_group, _ = Group.objects.get_or_create(name="Promo")

    def test_accounts_json_requires_login(self):
        """Test JSON view requires login."""
        response = self.client.get("/api/accounts.json")
        self.assertEqual(response.status_code, 302)

    def test_accounts_csv_requires_login(self):
        """Test CSV view requires login."""
        response = self.client.get("/api/accounts.csv")
        self.assertEqual(response.status_code, 302)

    def test_accounts_json_requires_group(self):
        """Test JSON view requires IT or Promo group."""
        self.login()
        response = self.client.get("/api/accounts.json")
        self.assertIn(response.status_code, [302, 403])

    def test_accounts_csv_requires_group(self):
        """Test CSV view requires IT or Promo group."""
        self.login()
        response = self.client.get("/api/accounts.csv")
        self.assertIn(response.status_code, [302, 403])

    def test_accounts_json_accessible_for_it_group(self):
        """Test JSON view accessible for IT group member."""
        self.login()
        self.user.groups.add(self.it_group)

        response = self.client.get("/api/accounts.json")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

    def test_accounts_csv_accessible_for_it_group(self):
        """Test CSV view accessible for IT group member."""
        self.login()
        self.user.groups.add(self.it_group)

        response = self.client.get("/api/accounts.csv")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv")

    def test_accounts_json_returns_user_data(self):
        """Test JSON view returns user data."""
        self.login()
        self.user.groups.add(self.it_group)

        response = self.client.get("/api/accounts.json")
        data = json.loads(response.content)

        self.assertIsInstance(data, list)
        # Should contain at least the current user
        self.assertGreaterEqual(len(data), 1)
        # Check structure
        first_item = data[0]
        self.assertIn("created_date", first_item)
        self.assertIn("is_active", first_item)
        self.assertIn("is_asleep", first_item)

    def test_accounts_csv_includes_empty_fields(self):
        """Test CSV view includes empty fields for consistency."""
        self.login()
        self.user.groups.add(self.it_group)

        response = self.client.get("/api/accounts.csv")
        content = response.content.decode("utf-8")

        # CSV should have headers including optional fields
        first_line = content.split("\n")[0]
        self.assertIn("created_date", first_line)
        self.assertIn("is_active", first_line)
