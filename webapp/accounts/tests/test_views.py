# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from unittest import mock

import pytz
from django.test import override_settings
from django.urls import reverse

from accounts.models import (
    VokoUser,
    EmailConfirmation,
    PasswordResetRequest,
    UserProfile,
)
from accounts.tests.factories import VokoUserFactory
from vokou.testing import VokoTestCase, suppressWarnings


class LoginViewTest(VokoTestCase):
    """Tests for the LoginView."""

    def setUp(self):
        self.user = VokoUserFactory.create(email="test@example.com")
        self.user.set_password("testpassword")
        self.user.is_active = True
        self.user.save()

    def test_login_page_renders(self):
        """Test login page renders correctly."""
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_successful_login(self):
        """Test successful login redirects."""
        data = {
            "username": "test@example.com",
            "password": "testpassword",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, 302)

    def test_invalid_credentials(self):
        """Test invalid credentials show error."""
        data = {
            "username": "test@example.com",
            "password": "wrongpassword",
        }
        response = self.client.post(reverse("login"), data)
        self.assertEqual(response.status_code, 200)
        self.assertIn("form", response.context)

    def test_login_with_next_parameter(self):
        """Test login redirects to next parameter."""
        data = {
            "username": "test@example.com",
            "password": "testpassword",
        }
        response = self.client.post(reverse("login") + "?next=/profile/", data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, "/profile/")

    def test_logged_in_user_redirected(self):
        """Test logged in user is redirected from login page."""
        self.login()
        response = self.client.get(reverse("login"))
        self.assertEqual(response.status_code, 302)


class RegisterViewTest(VokoTestCase):
    """Tests for the RegisterView."""

    @override_settings(CAPTCHA_ENABLED=False)
    def test_register_page_renders(self):
        """Test register page renders correctly."""
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")

    @override_settings(CAPTCHA_ENABLED=False)
    @mock.patch("accounts.models.mail_admins")
    @mock.patch("accounts.models.mail_user")
    @mock.patch("accounts.models.get_template_by_id")
    @mock.patch("accounts.models.render_mail_template")
    def test_successful_registration(self, mock_render, mock_get_template, mock_mail_user, mock_mail_admins):
        """Test successful registration creates user."""
        mock_render.return_value = ("Subject", "<html>", "text", "from@example.com")
        data = {
            "email": "newuser@example.com",
            "first_name": "New",
            "last_name": "User",
        }
        response = self.client.post(reverse("register"), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(VokoUser.objects.filter(email="newuser@example.com").exists())

    @override_settings(CAPTCHA_ENABLED=False)
    def test_registration_sends_confirmation_email(self):
        """Test registration sends confirmation email."""
        with mock.patch("accounts.models.mail_admins"):
            with mock.patch.object(EmailConfirmation, "send_confirmation_mail") as mock_send:
                data = {
                    "email": "newuser@example.com",
                    "first_name": "New",
                    "last_name": "User",
                }
                self.client.post(reverse("register"), data)
                mock_send.assert_called_once()

    def test_logged_in_user_redirected(self):
        """Test logged in user is redirected from register page."""
        self.login()
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 302)


class RegisterThanksViewTest(VokoTestCase):
    """Tests for the RegisterThanksView."""

    def test_thanks_page_renders(self):
        """Test thanks page renders correctly."""
        response = self.client.get(reverse("register_thanks"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register_thanks.html")


class LogoutViewTest(VokoTestCase):
    """Tests for the LogoutView."""

    def test_logout_redirects_to_login(self):
        """Test logout redirects to login page."""
        self.login()
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url)

    def test_logout_requires_login(self):
        """Test logout requires authentication."""
        response = self.client.get(reverse("logout"))
        self.assertEqual(response.status_code, 302)


class EmailConfirmViewTest(VokoTestCase):
    """Tests for the EmailConfirmView."""

    @mock.patch("accounts.models.mail_admins")
    def test_confirm_email(self, mock_mail):
        """Test confirming email works."""
        user = VokoUser.objects.create_user(email="test@example.com", first_name="Test", last_name="User")
        confirmation = user.email_confirmation
        self.assertFalse(confirmation.is_confirmed)

        response = self.client.get(reverse("confirm_email", kwargs={"pk": confirmation.token}))
        self.assertEqual(response.status_code, 200)

        confirmation.refresh_from_db()
        self.assertTrue(confirmation.is_confirmed)

    @suppressWarnings
    def test_already_confirmed_returns_404(self):
        """Test already confirmed token returns 404."""
        user = VokoUserFactory.create()
        confirmation = user.email_confirmation
        confirmation.is_confirmed = True
        confirmation.save()

        response = self.client.get(reverse("confirm_email", kwargs={"pk": confirmation.token}))
        self.assertEqual(response.status_code, 404)


class FinishRegistrationViewTest(VokoTestCase):
    """Tests for the FinishRegistration view."""

    @mock.patch("accounts.models.mail_admins")
    def test_finish_registration_page(self, mock_mail):
        """Test finish registration page renders for eligible user."""
        user = VokoUser.objects.create_user(email="test@example.com", first_name="Test", last_name="User")
        user.email_confirmation.is_confirmed = True
        user.email_confirmation.save()
        user.can_activate = True
        user.save()

        response = self.client.get(reverse("finish_registration", kwargs={"pk": user.email_confirmation.token}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/activate.html")

    @suppressWarnings
    @mock.patch("accounts.models.mail_admins")
    def test_finish_registration_invalid_token(self, mock_mail):
        """Test finish registration with invalid token returns 404."""
        response = self.client.get(reverse("finish_registration", kwargs={"pk": "invalid-token"}))
        self.assertEqual(response.status_code, 404)

    @suppressWarnings
    def test_finish_registration_already_active(self):
        """Test finish registration for active user returns 404."""
        user = VokoUserFactory.create(is_active=True)
        user.email_confirmation.is_confirmed = True
        user.email_confirmation.save()

        response = self.client.get(reverse("finish_registration", kwargs={"pk": user.email_confirmation.token}))
        self.assertEqual(response.status_code, 404)


class ProfileViewTest(VokoTestCase):
    """Tests for the ProfileView."""

    def test_profile_requires_login(self):
        """Test profile page requires login."""
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 302)

    def test_profile_page_renders(self):
        """Test profile page renders for logged in user."""
        self.login()
        UserProfile.objects.create(user=self.user)
        response = self.client.get(reverse("profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/profile.html")


class OrderHistoryViewTest(VokoTestCase):
    """Tests for the OrderHistory view."""

    def test_order_history_requires_login(self):
        """Test order history requires login."""
        response = self.client.get(reverse("order_history"))
        self.assertEqual(response.status_code, 302)

    def test_order_history_page_renders(self):
        """Test order history page renders for logged in user."""
        self.login()
        response = self.client.get(reverse("order_history"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/order_history.html")


class OverViewTest(VokoTestCase):
    """Tests for the OverView (dashboard)."""

    def _create_order_round(self):
        """Create an order round for tests that need it."""
        from ordering.models import OrderRound
        from datetime import datetime, timedelta
        import pytz

        now = datetime.now(pytz.utc)
        return OrderRound.objects.create(
            open_for_orders=now - timedelta(days=1),
            closed_for_orders=now + timedelta(days=1),
            collect_datetime=now + timedelta(days=2),
        )

    def test_overview_requires_login(self):
        """Test overview requires login."""
        response = self.client.get(reverse("overview"))
        self.assertEqual(response.status_code, 302)

    def test_overview_page_renders(self):
        """Test overview page renders for logged in user."""
        self._create_order_round()
        self.login()
        UserProfile.objects.create(user=self.user)
        response = self.client.get(reverse("overview"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/overview.html")

    def test_overview_context_contains_events(self):
        """Test overview context contains events list."""
        self._create_order_round()
        self.login()
        UserProfile.objects.create(user=self.user)
        response = self.client.get(reverse("overview"))
        self.assertIn("events", response.context)


class RequestPasswordResetViewTest(VokoTestCase):
    """Tests for the RequestPasswordResetView."""

    def test_password_reset_page_renders(self):
        """Test password reset page renders."""
        response = self.client.get(reverse("password_reset"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/passwordreset.html")

    @mock.patch("accounts.views.log")
    def test_password_reset_for_existing_user(self, mock_log):
        """Test password reset creates request for existing user."""
        VokoUserFactory.create(email="test@example.com")  # noqa: F841
        with mock.patch.object(PasswordResetRequest, "send_email") as mock_send:
            data = {"email": "test@example.com"}
            response = self.client.post(reverse("password_reset"), data)
            self.assertEqual(response.status_code, 302)
            mock_send.assert_called_once()

    @mock.patch("accounts.views.log")
    def test_password_reset_for_nonexistent_user(self, mock_log):
        """Test password reset for non-existent user doesn't fail."""
        data = {"email": "nonexistent@example.com"}
        response = self.client.post(reverse("password_reset"), data)
        # Should still redirect (don't reveal if email exists)
        self.assertEqual(response.status_code, 302)
        mock_log.log_event.assert_called_once()

    def test_logged_in_user_redirected(self):
        """Test logged in user is redirected from password reset page."""
        self.login()
        response = self.client.get(reverse("password_reset"))
        self.assertEqual(response.status_code, 302)


class PasswordResetViewTest(VokoTestCase):
    """Tests for the PasswordResetView."""

    def setUp(self):
        self.user = VokoUserFactory.create()
        self.user.set_password("oldpassword")
        self.user.save()
        self.reset_request = PasswordResetRequest.objects.create(user=self.user)

    def test_password_reset_page_renders(self):
        """Test password reset page renders for valid token."""
        response = self.client.get(reverse("reset_pass", kwargs={"pk": self.reset_request.token}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/passwordreset_reset.html")

    @suppressWarnings
    def test_expired_token_returns_404(self):
        """Test expired token returns 404."""
        self.reset_request.created = datetime.now(pytz.utc) - timedelta(hours=25)
        self.reset_request.save()

        response = self.client.get(reverse("reset_pass", kwargs={"pk": self.reset_request.token}))
        self.assertEqual(response.status_code, 404)

    @suppressWarnings
    def test_used_token_returns_404(self):
        """Test used token returns 404."""
        self.reset_request.is_used = True
        self.reset_request.save()

        response = self.client.get(reverse("reset_pass", kwargs={"pk": self.reset_request.token}))
        self.assertEqual(response.status_code, 404)

    def test_successful_password_reset(self):
        """Test successful password reset."""
        data = {
            "password1": "newpassword123",
            "password2": "newpassword123",
        }
        response = self.client.post(reverse("reset_pass", kwargs={"pk": self.reset_request.token}), data)
        self.assertEqual(response.status_code, 302)

        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("newpassword123"))

        # Verify request is marked as used
        self.reset_request.refresh_from_db()
        self.assertTrue(self.reset_request.is_used)

    def test_password_mismatch(self):
        """Test password mismatch shows error."""
        data = {
            "password1": "newpassword123",
            "password2": "differentpassword",
        }
        response = self.client.post(reverse("reset_pass", kwargs={"pk": self.reset_request.token}), data)
        self.assertEqual(response.status_code, 200)


class EditProfileViewTest(VokoTestCase):
    """Tests for the EditProfileView."""

    def test_edit_profile_requires_login(self):
        """Test edit profile requires login."""
        response = self.client.get(reverse("update_profile"))
        self.assertEqual(response.status_code, 302)

    def test_edit_profile_page_renders(self):
        """Test edit profile page renders."""
        self.login()
        UserProfile.objects.create(user=self.user)
        response = self.client.get(reverse("update_profile"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/update_profile.html")

    def test_edit_profile_success_message(self):
        """Test successful edit shows success message."""
        self.login()
        UserProfile.objects.create(user=self.user)
        data = {
            "first_name": "Updated",
            "last_name": "Name",
        }
        response = self.client.post(reverse("update_profile"), data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertMsgInResponse(response, "Je profiel is aangepast.")


class ContactViewTest(VokoTestCase):
    """Tests for the Contact view."""

    def test_contact_requires_login(self):
        """Test contact page requires login."""
        response = self.client.get(reverse("contact"))
        self.assertEqual(response.status_code, 302)

    def test_contact_page_renders(self):
        """Test contact page renders."""
        self.login()
        response = self.client.get(reverse("contact"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/contact.html")


class WelcomeViewTest(VokoTestCase):
    """Tests for the WelcomeView."""

    def test_welcome_page_renders(self):
        """Test welcome page renders."""
        response = self.client.get("/accounts/welcome/")
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/welcome.html")
