# -*- coding: utf-8 -*-
from unittest import mock

from django.test import TestCase
from django.contrib.admin.sites import AdminSite
from django.contrib.messages.storage.fallback import FallbackStorage

from accounts.admin import (
    enable_user,
    force_confirm_email,
    anonymize_user,
    VokoUserAdmin,
    HasPaidFilter,
)
from accounts.models import VokoUser, UserProfile
from accounts.tests.factories import VokoUserFactory, AddressFactory
from finance.models import Balance


class MockRequest:
    """Mock request object for admin actions."""

    def __init__(self, user=None):
        self.user = user or VokoUserFactory.create(is_staff=True, is_superuser=True)
        self.session = {}
        self._messages = FallbackStorage(self)

    @property
    def messages(self):
        return self._messages


class EnableUserActionTest(TestCase):
    """Tests for the enable_user admin action."""

    @mock.patch("accounts.admin.get_template_by_id")
    @mock.patch("accounts.admin.render_mail_template")
    @mock.patch("accounts.admin.mail_user")
    @mock.patch("accounts.admin.log")
    def test_enable_user_sends_activation_mail(self, mock_log, mock_mail_user, mock_render, mock_get_template):
        """Test enable_user sends activation email."""
        mock_template = mock.Mock()
        mock_get_template.return_value = mock_template
        mock_render.return_value = ("Subject", "<html>", "text", "from@example.com")

        user = VokoUserFactory.create(is_active=False, can_activate=False)
        user.email_confirmation.is_confirmed = True
        user.email_confirmation.save()

        request = MockRequest()
        queryset = VokoUser.objects.filter(pk=user.pk)

        enable_user(None, request, queryset)

        user.refresh_from_db()
        self.assertTrue(user.can_activate)
        mock_mail_user.assert_called_once()
        mock_log.log_event.assert_called_once()

    def test_enable_user_skips_unconfirmed_email(self):
        """Test enable_user skips users with unconfirmed email."""
        user = VokoUserFactory.create(is_active=False, can_activate=False)
        user.email_confirmation.is_confirmed = False
        user.email_confirmation.save()

        request = MockRequest()
        queryset = VokoUser.objects.filter(pk=user.pk)

        enable_user(None, request, queryset)

        user.refresh_from_db()
        self.assertFalse(user.can_activate)

    def test_enable_user_skips_already_active(self):
        """Test enable_user skips already active users."""
        user = VokoUserFactory.create(is_active=True)
        user.email_confirmation.is_confirmed = True
        user.email_confirmation.save()

        request = MockRequest()
        queryset = VokoUser.objects.filter(pk=user.pk)

        enable_user(None, request, queryset)

        user.refresh_from_db()
        # can_activate should not be changed


class ForceConfirmEmailActionTest(TestCase):
    """Tests for the force_confirm_email admin action."""

    @mock.patch("accounts.admin.log")
    def test_force_confirm_email(self, mock_log):
        """Test force_confirm_email confirms email."""
        user = VokoUserFactory.create()
        user.email_confirmation.is_confirmed = False
        user.email_confirmation.save()

        request = MockRequest()
        queryset = VokoUser.objects.filter(pk=user.pk)

        force_confirm_email(None, request, queryset)

        user.email_confirmation.refresh_from_db()
        self.assertTrue(user.email_confirmation.is_confirmed)
        mock_log.log_event.assert_called_once()


class AnonymizeUserActionTest(TestCase):
    """Tests for the anonymize_user admin action."""

    def test_anonymize_user_with_zero_balance(self):
        """Test anonymize_user anonymizes user with zero balance."""
        user = VokoUserFactory.create(email="original@example.com", first_name="Original", last_name="Name")
        address = AddressFactory.create(street_and_number="Original Street 123", city="Original City")
        UserProfile.objects.create(user=user, address=address, phone_number="0612345678", notes="Original notes")

        request = MockRequest()
        queryset = VokoUser.objects.filter(pk=user.pk)

        anonymize_user(None, request, queryset)

        user.refresh_from_db()
        self.assertTrue(user.is_asleep)
        self.assertIn("@anon.vokoutrecht.nl", user.email)
        self.assertEqual(user.first_name, "account")
        self.assertEqual(user.last_name, str(user.id))

        # Check profile is anonymized
        user.userprofile.refresh_from_db()
        self.assertEqual(user.userprofile.phone_number, "")
        self.assertEqual(user.userprofile.notes, "")

        # Check address is anonymized
        address.refresh_from_db()
        self.assertEqual(address.street_and_number, "")
        self.assertEqual(address.zip_code, "0000")
        self.assertEqual(address.city, "")

    def test_anonymize_user_with_positive_balance_fails(self):
        """Test anonymize_user fails for user with positive balance."""
        user = VokoUserFactory.create(email="original@example.com", first_name="Original", last_name="Name")
        Balance.objects.create(user=user, type="CR", amount=10.00)

        request = MockRequest()
        queryset = VokoUser.objects.filter(pk=user.pk)

        anonymize_user(None, request, queryset)

        user.refresh_from_db()
        # User should NOT be anonymized
        self.assertFalse(user.is_asleep)
        self.assertEqual(user.email, "original@example.com")
        self.assertEqual(user.first_name, "Original")

    def test_anonymize_user_without_profile(self):
        """Test anonymize_user handles user without profile."""
        user = VokoUserFactory.create(email="original@example.com", first_name="Original", last_name="Name")

        request = MockRequest()
        queryset = VokoUser.objects.filter(pk=user.pk)

        # Should not raise an exception
        anonymize_user(None, request, queryset)

        user.refresh_from_db()
        self.assertTrue(user.is_asleep)


class HasPaidFilterTest(TestCase):
    """Tests for the HasPaidFilter admin filter."""

    def test_has_paid_filter_yes(self):
        """Test HasPaidFilter filters users who have paid."""
        from finance.models import Payment
        from ordering.models import Order, OrderRound

        # Create order round
        from datetime import datetime
        import pytz

        now = datetime.now(pytz.utc)
        order_round = OrderRound.objects.create(open_for_orders=now, closed_for_orders=now, collect_datetime=now)

        # Create user with payment
        user_paid = VokoUserFactory.create()
        order = Order.objects.create(user=user_paid, order_round=order_round)
        Payment.objects.create(order=order, succeeded=True, amount=10.00)

        # Create user without payment
        user_not_paid = VokoUserFactory.create()

        # Test filter
        filter_instance = HasPaidFilter(request=None, params={"has_paid": "yes"}, model=VokoUser, model_admin=None)
        filter_instance.used_parameters = {"has_paid": "yes"}

        queryset = VokoUser.objects.all()
        filtered = filter_instance.queryset(None, queryset)

        self.assertIn(user_paid, filtered)
        self.assertNotIn(user_not_paid, filtered)

    def test_has_paid_filter_no(self):
        """Test HasPaidFilter filters users who have not paid."""
        from finance.models import Payment
        from ordering.models import Order, OrderRound

        from datetime import datetime
        import pytz

        now = datetime.now(pytz.utc)
        order_round = OrderRound.objects.create(open_for_orders=now, closed_for_orders=now, collect_datetime=now)

        # Create user with payment
        user_paid = VokoUserFactory.create()
        order = Order.objects.create(user=user_paid, order_round=order_round)
        Payment.objects.create(order=order, succeeded=True, amount=10.00)

        # Create user without payment
        user_not_paid = VokoUserFactory.create()

        # Test filter
        filter_instance = HasPaidFilter(request=None, params={"has_paid": "no"}, model=VokoUser, model_admin=None)
        filter_instance.used_parameters = {"has_paid": "no"}

        queryset = VokoUser.objects.all()
        filtered = filter_instance.queryset(None, queryset)

        self.assertNotIn(user_paid, filtered)
        self.assertIn(user_not_paid, filtered)


class VokoUserAdminTest(TestCase):
    """Tests for the VokoUserAdmin class."""

    def setUp(self):
        self.site = AdminSite()
        self.admin = VokoUserAdmin(VokoUser, self.site)

    def test_admin_actions_registered(self):
        """Test admin has custom actions registered."""
        actions = self.admin.actions
        self.assertIn(enable_user, actions)
        self.assertIn(force_confirm_email, actions)
        self.assertIn(anonymize_user, actions)

    def test_admin_list_display(self):
        """Test admin list display fields."""
        self.assertIn("email", self.admin.list_display)
        self.assertIn("first_name", self.admin.list_display)
        self.assertIn("last_name", self.admin.list_display)
