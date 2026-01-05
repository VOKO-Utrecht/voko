# -*- coding: utf-8 -*-
from unittest import mock

from django.test import TestCase

from accounts.forms import (
    VokoUserCreationForm,
    VokoUserFinishForm,
    VokoUserChangeForm,
    RequestPasswordResetForm,
    PasswordResetForm,
    ChangeProfileForm,
)
from accounts.models import UserProfile
from accounts.tests.factories import VokoUserFactory


class VokoUserCreationFormTest(TestCase):
    """Tests for the VokoUserCreationForm."""

    def test_valid_form(self):
        """Test form is valid with correct data."""
        data = {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
        }
        form = VokoUserCreationForm(data=data)
        self.assertTrue(form.is_valid())

    def test_email_required(self):
        """Test email is required."""
        data = {
            "email": "",
            "first_name": "Test",
            "last_name": "User",
        }
        form = VokoUserCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_first_name_required(self):
        """Test first name is required."""
        data = {
            "email": "test@example.com",
            "first_name": "",
            "last_name": "User",
        }
        form = VokoUserCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("first_name", form.errors)

    def test_last_name_required(self):
        """Test last name is required."""
        data = {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "",
        }
        form = VokoUserCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("last_name", form.errors)

    def test_email_lowercased_on_save(self):
        """Test email is lowercased when saving."""
        data = {
            "email": "Test@EXAMPLE.COM",
            "first_name": "Test",
            "last_name": "User",
        }
        form = VokoUserCreationForm(data=data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.email, "test@example.com")

    def test_duplicate_email_rejected(self):
        """Test duplicate email addresses are rejected."""
        VokoUserFactory.create(email="existing@example.com")
        data = {
            "email": "existing@example.com",
            "first_name": "Test",
            "last_name": "User",
        }
        form = VokoUserCreationForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class VokoUserFinishFormTest(TestCase):
    """Tests for the VokoUserFinishForm."""

    def setUp(self):
        self.user = VokoUserFactory.create(is_active=False)

    def test_valid_form(self):
        """Test form is valid with correct data."""
        data = {
            "phone_number": "0612345678",
            "password1": "testpassword123",
            "password2": "testpassword123",
            "notes": "Test notes",
            "has_drivers_license": True,
            "accept_terms_and_privacy": True,
        }
        form = VokoUserFinishForm(data=data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_password_mismatch(self):
        """Test passwords must match."""
        data = {
            "phone_number": "0612345678",
            "password1": "testpassword123",
            "password2": "differentpassword",
            "notes": "Test notes",
            "accept_terms_and_privacy": True,
        }
        form = VokoUserFinishForm(data=data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_accept_terms_required(self):
        """Test accepting terms and privacy is required."""
        data = {
            "phone_number": "0612345678",
            "password1": "testpassword123",
            "password2": "testpassword123",
            "notes": "Test notes",
            "accept_terms_and_privacy": False,
        }
        form = VokoUserFinishForm(data=data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("accept_terms_and_privacy", form.errors)

    def test_notes_required(self):
        """Test notes is required."""
        data = {
            "phone_number": "0612345678",
            "password1": "testpassword123",
            "password2": "testpassword123",
            "notes": "",
            "accept_terms_and_privacy": True,
        }
        form = VokoUserFinishForm(data=data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("notes", form.errors)

    @mock.patch("accounts.forms.mail_admins")
    def test_save_activates_user(self, mock_mail):
        """Test save activates the user."""
        data = {
            "phone_number": "0612345678",
            "password1": "testpassword123",
            "password2": "testpassword123",
            "notes": "Test notes",
            "accept_terms_and_privacy": True,
        }
        form = VokoUserFinishForm(data=data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.is_active)
        self.assertIsNotNone(user.activated)

    @mock.patch("accounts.forms.mail_admins")
    def test_save_creates_user_profile(self, mock_mail):
        """Test save creates a UserProfile."""
        data = {
            "phone_number": "0612345678",
            "password1": "testpassword123",
            "password2": "testpassword123",
            "notes": "Test notes",
            "has_drivers_license": True,
            "accept_terms_and_privacy": True,
        }
        form = VokoUserFinishForm(data=data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.phone_number, "0612345678")
        self.assertEqual(profile.notes, "Test notes")

    @mock.patch("accounts.forms.mail_admins")
    def test_save_sets_password(self, mock_mail):
        """Test save sets the password correctly."""
        data = {
            "phone_number": "0612345678",
            "password1": "testpassword123",
            "password2": "testpassword123",
            "notes": "Test notes",
            "accept_terms_and_privacy": True,
        }
        form = VokoUserFinishForm(data=data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.check_password("testpassword123"))


class VokoUserChangeFormTest(TestCase):
    """Tests for the VokoUserChangeForm."""

    def setUp(self):
        self.user = VokoUserFactory.create()
        self.user.set_password("testpass")
        self.user.save()

    def test_password_field_readonly(self):
        """Test password field returns initial value."""
        form = VokoUserChangeForm(instance=self.user)
        # Password should be read-only
        self.assertIn("password", form.fields)

    def test_clean_prevents_sleeping_user_with_balance(self):
        """Test user with balance cannot be set to sleeping."""
        # Create a balance for the user
        from finance.models import Balance

        Balance.objects.create(user=self.user, type="CR", amount=10.00)

        data = {
            "email": self.user.email,
            "first_name": self.user.first_name,
            "last_name": self.user.last_name,
            "password": self.user.password,
            "is_asleep": True,
            "is_active": self.user.is_active,
            "is_admin": self.user.is_admin,
            "is_staff": self.user.is_staff,
            "can_activate": self.user.can_activate,
        }
        form = VokoUserChangeForm(data=data, instance=self.user)
        self.assertFalse(form.is_valid())


class RequestPasswordResetFormTest(TestCase):
    """Tests for the RequestPasswordResetForm."""

    def test_valid_form(self):
        """Test form is valid with email."""
        data = {"email": "test@example.com"}
        form = RequestPasswordResetForm(data=data)
        self.assertTrue(form.is_valid())

    def test_invalid_email(self):
        """Test form is invalid with bad email."""
        data = {"email": "not-an-email"}
        form = RequestPasswordResetForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_email_required(self):
        """Test email is required."""
        data = {"email": ""}
        form = RequestPasswordResetForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)


class PasswordResetFormTest(TestCase):
    """Tests for the PasswordResetForm."""

    def test_valid_form(self):
        """Test form is valid with matching passwords."""
        data = {
            "password1": "newpassword123",
            "password2": "newpassword123",
        }
        form = PasswordResetForm(data=data)
        self.assertTrue(form.is_valid())

    def test_password_mismatch(self):
        """Test passwords must match."""
        data = {
            "password1": "newpassword123",
            "password2": "differentpassword",
        }
        form = PasswordResetForm(data=data)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_passwords_required(self):
        """Test both passwords are required."""
        form = PasswordResetForm(data={"password1": "", "password2": ""})
        self.assertFalse(form.is_valid())


class ChangeProfileFormTest(TestCase):
    """Tests for the ChangeProfileForm."""

    def setUp(self):
        self.user = VokoUserFactory.create()
        UserProfile.objects.create(user=self.user)

    def test_valid_form(self):
        """Test form is valid with correct data."""
        data = {
            "first_name": "Updated",
            "last_name": "Name",
            "phone_number": "0612345678",
        }
        form = ChangeProfileForm(data=data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_password_change(self):
        """Test password can be changed."""
        data = {
            "first_name": "Updated",
            "last_name": "Name",
            "password1": "newpassword123",
            "password2": "newpassword123",
        }
        form = ChangeProfileForm(data=data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.check_password("newpassword123"))

    def test_password_mismatch(self):
        """Test passwords must match."""
        data = {
            "first_name": "Updated",
            "last_name": "Name",
            "password1": "newpassword123",
            "password2": "differentpassword",
        }
        form = ChangeProfileForm(data=data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)

    def test_shares_car_requires_details(self):
        """Test car details required when shares_car is True."""
        data = {
            "first_name": "Updated",
            "last_name": "Name",
            "shares_car": True,
            "car_neighborhood": "",
            "car_type": "",
        }
        form = ChangeProfileForm(data=data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn("car_neighborhood", form.errors)
        self.assertIn("car_type", form.errors)

    def test_shares_car_with_details(self):
        """Test form valid when car details provided."""
        data = {
            "first_name": "Updated",
            "last_name": "Name",
            "shares_car": True,
            "car_neighborhood": "Centrum",
            "car_type": "Station",
        }
        form = ChangeProfileForm(data=data, instance=self.user)
        self.assertTrue(form.is_valid())

    def test_save_updates_profile(self):
        """Test save updates user profile."""
        data = {
            "first_name": "Updated",
            "last_name": "Name",
            "phone_number": "0612345678",
            "has_drivers_license": True,
            "particularities": "Test particularities",
        }
        form = ChangeProfileForm(data=data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        profile = user.userprofile
        self.assertEqual(profile.phone_number, "0612345678")
        self.assertTrue(profile.has_drivers_license)
        self.assertEqual(profile.particularities, "Test particularities")

    def test_initial_values_from_profile(self):
        """Test form initial values come from profile."""
        self.user.userprofile.phone_number = "0698765432"
        self.user.userprofile.has_drivers_license = True
        self.user.userprofile.save()

        form = ChangeProfileForm(instance=self.user)
        self.assertEqual(form.fields["phone_number"].initial, "0698765432")
        self.assertTrue(form.fields["has_drivers_license"].initial)

    def test_orderround_mail_optout(self):
        """Test orderround mail optout can be set."""
        data = {
            "first_name": "Updated",
            "last_name": "Name",
            "orderround_mail_optout": True,
        }
        form = ChangeProfileForm(data=data, instance=self.user)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertTrue(user.userprofile.orderround_mail_optout)
