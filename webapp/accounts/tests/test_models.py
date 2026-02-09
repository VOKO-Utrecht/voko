# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from unittest import mock

import pytz
from django.test import TestCase
from django.contrib.auth.models import Group

from accounts.models import (
    Address,
    UserProfile,
    VokoUser,
    PasswordResetRequest,
    ReadOnlyVokoUser,
    SleepingVokoUser,
)
from accounts.tests.factories import VokoUserFactory, AddressFactory


class AddressModelTest(TestCase):
    """Tests for the Address model."""

    def test_str_representation(self):
        """Test string representation of Address."""
        address = Address.objects.create(street_and_number="Oudegracht 123", zip_code="3511AB", city="Utrecht")
        self.assertEqual(str(address), "Oudegracht 123 - 3511AB, Utrecht")

    def test_address_with_empty_fields(self):
        """Test address can be created with minimal fields."""
        address = Address.objects.create(zip_code="1234AB")
        self.assertEqual(address.street_and_number, "")
        self.assertEqual(address.city, "")


class UserProfileModelTest(TestCase):
    """Tests for the UserProfile model."""

    def test_str_representation(self):
        """Test string representation of UserProfile."""
        user = VokoUserFactory.create(first_name="Jan", last_name="Janssen")
        profile = UserProfile.objects.create(user=user)
        self.assertIn("Jan Janssen", str(profile))

    def test_profile_with_address(self):
        """Test profile can be linked to an address."""
        user = VokoUserFactory.create()
        address = AddressFactory.create()
        profile = UserProfile.objects.create(user=user, address=address)
        self.assertEqual(profile.address, address)

    def test_profile_default_values(self):
        """Test default values for UserProfile fields."""
        user = VokoUserFactory.create()
        profile = UserProfile.objects.create(user=user)
        self.assertFalse(profile.has_drivers_license)
        self.assertFalse(profile.shares_car)
        self.assertFalse(profile.orderround_mail_optout)
        self.assertEqual(profile.car_neighborhood, "")
        self.assertEqual(profile.car_type, "")


class VokoUserManagerTest(TestCase):
    """Tests for the VokoUserManager."""

    def test_create_user(self):
        """Test creating a regular user."""
        user = VokoUser.objects.create_user(
            email="test@example.com", first_name="Test", last_name="User", password="testpassword123"
        )
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.first_name, "Test")
        self.assertEqual(user.last_name, "User")
        self.assertTrue(user.check_password("testpassword123"))
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_admin)
        self.assertFalse(user.is_staff)

    def test_create_user_without_email_raises_error(self):
        """Test creating a user without email raises ValueError."""
        with self.assertRaises(ValueError) as context:
            VokoUser.objects.create_user(email="", first_name="Test", last_name="User")
        self.assertIn("email address", str(context.exception))

    def test_create_superuser(self):
        """Test creating a superuser."""
        user = VokoUser.objects.create_superuser(
            email="admin@example.com", first_name="Admin", last_name="User", password="adminpassword123"
        )
        self.assertEqual(user.email, "admin@example.com")
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_admin)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertIsNotNone(user.activated)

    def test_email_normalization(self):
        """Test that email is normalized."""
        user = VokoUser.objects.create_user(email="Test@EXAMPLE.COM", first_name="Test", last_name="User")
        # Email should be normalized (lowercase domain)
        self.assertEqual(user.email, "Test@example.com")

    def test_queryset_excludes_sleeping_users(self):
        """Test that default queryset excludes sleeping users."""
        active_user = VokoUserFactory.create(is_asleep=False)
        sleeping_user = VokoUser.objects.create_user(
            email="sleeping@example.com", first_name="Sleeping", last_name="User"
        )
        sleeping_user.is_asleep = True
        sleeping_user.save()

        # Default manager should exclude sleeping users
        users = VokoUser.objects.all()
        self.assertIn(active_user, users)
        # sleeping user should not be in normal queryset


class VokoUserModelTest(TestCase):
    """Tests for the VokoUser model."""

    def test_str_representation(self):
        """Test string representation of VokoUser."""
        user = VokoUserFactory.create(first_name="Jan", last_name="Janssen")
        self.assertEqual(str(user), "Jan Janssen")

    def test_get_full_name(self):
        """Test get_full_name returns correct format."""
        user = VokoUserFactory.create(first_name="Jan", last_name="Janssen")
        self.assertEqual(user.get_full_name(), "Jan Janssen")

    def test_get_short_name(self):
        """Test get_short_name returns email."""
        user = VokoUserFactory.create(email="jan@example.com")
        self.assertEqual(user.get_short_name(), "jan@example.com")

    def test_is_coordinator_with_uitdeelcoordinatoren(self):
        """Test is_coordinator returns True for Uitdeelcoordinatoren."""
        user = VokoUserFactory.create()
        group = Group.objects.create(name="Uitdeelcoordinatoren")
        user.groups.add(group)
        self.assertTrue(user.is_coordinator())

    def test_is_coordinator_with_transportcoordinatoren(self):
        """Test is_coordinator returns True for Transportcoordinatoren."""
        user = VokoUserFactory.create()
        group = Group.objects.create(name="Transportcoordinatoren")
        user.groups.add(group)
        self.assertTrue(user.is_coordinator())

    def test_is_coordinator_with_other_group(self):
        """Test is_coordinator returns False for other groups."""
        user = VokoUserFactory.create()
        group = Group.objects.create(name="OtherGroup")
        user.groups.add(group)
        self.assertFalse(user.is_coordinator())

    def test_flat_groups(self):
        """Test flat_groups returns list of group names."""
        user = VokoUserFactory.create()
        group1 = Group.objects.create(name="Group1")
        group2 = Group.objects.create(name="Group2")
        user.groups.add(group1, group2)
        flat = list(user.flat_groups())
        self.assertIn("Group1", flat)
        self.assertIn("Group2", flat)

    @mock.patch("accounts.models.mail_admins")
    def test_save_sends_mail_on_create(self, mock_mail_admins):
        """Test that creating a user sends mail to admins."""
        user = VokoUser(email="new@example.com", first_name="New", last_name="User")
        user.set_password("test123")
        user.save()
        mock_mail_admins.assert_called_once()

    def test_save_creates_email_confirmation(self):
        """Test that saving a new user creates EmailConfirmation."""
        user = VokoUser.objects.create_user(email="test@example.com", first_name="Test", last_name="User")
        self.assertTrue(hasattr(user, "email_confirmation"))
        self.assertIsNotNone(user.email_confirmation)

    def test_username_field_is_email(self):
        """Test USERNAME_FIELD is email."""
        self.assertEqual(VokoUser.USERNAME_FIELD, "email")


class EmailConfirmationModelTest(TestCase):
    """Tests for the EmailConfirmation model."""

    def test_token_generated_on_save(self):
        """Test that token is generated when saving."""
        user = VokoUserFactory.create()
        # EmailConfirmation is auto-created
        self.assertIsNotNone(user.email_confirmation.token)
        self.assertEqual(len(user.email_confirmation.token), 36)  # UUID length

    def test_confirm_sets_is_confirmed_true(self):
        """Test confirm method sets is_confirmed to True."""
        user = VokoUserFactory.create()
        confirmation = user.email_confirmation
        self.assertFalse(confirmation.is_confirmed)
        confirmation.confirm()
        self.assertTrue(confirmation.is_confirmed)

    def test_str_representation(self):
        """Test string representation of EmailConfirmation."""
        user = VokoUserFactory.create(first_name="Jan", last_name="Janssen", email="jan@example.com")
        confirmation = user.email_confirmation
        str_repr = str(confirmation)
        self.assertIn("Jan Janssen", str_repr)
        self.assertIn("jan@example.com", str_repr)
        self.assertIn("False", str_repr)  # Not confirmed

    @mock.patch("accounts.models.get_template_by_id")
    @mock.patch("accounts.models.render_mail_template")
    @mock.patch("accounts.models.mail_user")
    def test_send_confirmation_mail(self, mock_mail_user, mock_render, mock_get_template):
        """Test send_confirmation_mail calls mail functions."""
        mock_template = mock.Mock()
        mock_get_template.return_value = mock_template
        mock_render.return_value = ("Subject", "<html>", "text", "from@example.com")

        user = VokoUserFactory.create()
        user.email_confirmation.send_confirmation_mail()

        mock_get_template.assert_called_once()
        mock_render.assert_called_once()
        mock_mail_user.assert_called_once()


class PasswordResetRequestModelTest(TestCase):
    """Tests for the PasswordResetRequest model."""

    def test_token_generated_on_save(self):
        """Test that token is generated when saving."""
        user = VokoUserFactory.create()
        request = PasswordResetRequest.objects.create(user=user)
        self.assertIsNotNone(request.token)
        self.assertEqual(len(request.token), 36)  # UUID length

    def test_is_usable_when_fresh(self):
        """Test is_usable is True for fresh request."""
        user = VokoUserFactory.create()
        request = PasswordResetRequest.objects.create(user=user)
        self.assertTrue(request.is_usable)

    def test_is_usable_when_used(self):
        """Test is_usable is False when already used."""
        user = VokoUserFactory.create()
        request = PasswordResetRequest.objects.create(user=user, is_used=True)
        self.assertFalse(request.is_usable)

    def test_is_usable_when_expired(self):
        """Test is_usable is False after 24 hours."""
        user = VokoUserFactory.create()
        request = PasswordResetRequest.objects.create(user=user)
        # Simulate old request
        request.created = datetime.now(pytz.utc) - timedelta(hours=25)
        request.save()
        self.assertFalse(request.is_usable)

    def test_is_usable_within_24_hours(self):
        """Test is_usable is True within 24 hours."""
        user = VokoUserFactory.create()
        request = PasswordResetRequest.objects.create(user=user)
        # Simulate request 23 hours ago
        request.created = datetime.now(pytz.utc) - timedelta(hours=23)
        request.save()
        self.assertTrue(request.is_usable)

    def test_str_representation(self):
        """Test string representation."""
        user = VokoUserFactory.create(first_name="Jan", last_name="Janssen")
        request = PasswordResetRequest.objects.create(user=user)
        str_repr = str(request)
        self.assertIn("Jan Janssen", str_repr)
        self.assertIn("Used: False", str_repr)
        self.assertIn("Usable: True", str_repr)

    @mock.patch("accounts.models.get_template_by_id")
    @mock.patch("accounts.models.render_mail_template")
    @mock.patch("accounts.models.mail_user")
    def test_send_email(self, mock_mail_user, mock_render, mock_get_template):
        """Test send_email calls mail functions."""
        mock_template = mock.Mock()
        mock_get_template.return_value = mock_template
        mock_render.return_value = ("Subject", "<html>", "text", "from@example.com")

        user = VokoUserFactory.create()
        request = PasswordResetRequest.objects.create(user=user)
        request.send_email()

        mock_get_template.assert_called_once()
        mock_render.assert_called_once()
        mock_mail_user.assert_called_once()


class ProxyModelsTest(TestCase):
    """Tests for proxy models."""

    def test_readonly_voko_user_is_proxy(self):
        """Test ReadOnlyVokoUser is a proxy model."""
        self.assertTrue(ReadOnlyVokoUser._meta.proxy)

    def test_sleeping_voko_user_is_proxy(self):
        """Test SleepingVokoUser is a proxy model."""
        self.assertTrue(SleepingVokoUser._meta.proxy)

    def test_sleeping_voko_user_manager_filters_sleeping(self):
        """Test SleepingVokoUser manager only returns sleeping users."""
        # Create a regular user
        regular_user = VokoUserFactory.create(is_asleep=False)

        # Create a sleeping user
        sleeping_user = VokoUser.objects.create_user(
            email="sleeping@example.com", first_name="Sleeping", last_name="User"
        )
        sleeping_user.is_asleep = True
        sleeping_user.save()

        # SleepingVokoUser should only show sleeping users
        sleeping_users = SleepingVokoUser.objects.all()
        self.assertIn(sleeping_user, sleeping_users)
        self.assertNotIn(regular_user, sleeping_users)
