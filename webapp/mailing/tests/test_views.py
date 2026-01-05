# -*- coding: utf-8 -*-
from unittest import mock

from django.urls import reverse

from mailing.models import MailTemplate
from accounts.tests.factories import VokoUserFactory
from vokou.testing import VokoTestCase


class ChooseTemplateViewTest(VokoTestCase):
    """Tests for the ChooseTemplateView."""

    def test_requires_login(self):
        """Test view requires login."""
        response = self.client.get(reverse("admin_choose_mail_template"))
        self.assertEqual(response.status_code, 302)

    def test_requires_staff(self):
        """Test view requires staff user."""
        self.login()
        response = self.client.get(reverse("admin_choose_mail_template"))
        self.assertEqual(response.status_code, 302)

    def test_staff_can_access(self):
        """Test staff user can access."""
        self.login()
        self.user.is_staff = True
        self.user.save()
        response = self.client.get(reverse("admin_choose_mail_template"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mailing/admin/mailtemplate_list.html")

    def test_lists_templates(self):
        """Test view lists mail templates."""
        self.login()
        self.user.is_staff = True
        self.user.save()

        template = MailTemplate.objects.create(title="Test Template", html_body="<p>Test</p>")

        response = self.client.get(reverse("admin_choose_mail_template"))
        self.assertIn(template, response.context["object_list"])


class PreviewMailViewTest(VokoTestCase):
    """Tests for the PreviewMailView."""

    def setUp(self):
        super().setUp()
        self.template = MailTemplate.objects.create(
            title="Test Template", subject="Test {{ user.first_name }}", html_body="<p>Hello {{ user.first_name }}</p>"
        )

    def test_requires_login(self):
        """Test view requires login."""
        response = self.client.get(reverse("admin_preview_mail", kwargs={"pk": self.template.pk}))
        self.assertEqual(response.status_code, 302)

    def test_requires_staff(self):
        """Test view requires staff user."""
        self.login()
        response = self.client.get(reverse("admin_preview_mail", kwargs={"pk": self.template.pk}))
        self.assertEqual(response.status_code, 302)

    def test_staff_can_access(self):
        """Test staff user can access."""
        self.login()
        self.user.is_staff = True
        self.user.save()

        # Set up session with user IDs
        session = self.client.session
        session["mailing_user_ids"] = [self.user.pk]
        session.save()

        response = self.client.get(reverse("admin_preview_mail", kwargs={"pk": self.template.pk}))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "mailing/admin/preview_mail.html")

    def test_context_contains_template(self):
        """Test context contains the template."""
        self.login()
        self.user.is_staff = True
        self.user.save()

        session = self.client.session
        session["mailing_user_ids"] = [self.user.pk]
        session.save()

        response = self.client.get(reverse("admin_preview_mail", kwargs={"pk": self.template.pk}))
        self.assertEqual(response.context["template"], self.template)

    def test_context_contains_example_render(self):
        """Test context contains example rendering."""
        self.login()
        self.user.is_staff = True
        self.user.save()

        session = self.client.session
        session["mailing_user_ids"] = [self.user.pk]
        session.save()

        response = self.client.get(reverse("admin_preview_mail", kwargs={"pk": self.template.pk}))
        self.assertIn("example", response.context)


class SendMailViewTest(VokoTestCase):
    """Tests for the SendMailView."""

    def setUp(self):
        super().setUp()
        self.template = MailTemplate.objects.create(
            title="Test Template", subject="Test Subject", html_body="<p>Hello {{ user.first_name }}</p>"
        )

    def _setup_session_with_user_ids(self, user_ids):
        """Helper to set up session with mailing_user_ids."""
        session = self.client.session
        session["mailing_user_ids"] = user_ids
        session.save()

    def test_requires_staff(self):
        """Test view requires staff user."""
        self.login()
        self._setup_session_with_user_ids([self.user.pk])
        response = self.client.get(reverse("admin_send_mail", kwargs={"pk": self.template.pk}))
        self.assertEqual(response.status_code, 302)

    @mock.patch("mailing.views.mail_user")
    @mock.patch("mailing.views.log_event")
    def test_sends_mail_to_users(self, mock_log, mock_mail_user):
        """Test sends mail to users in session."""
        self.login()
        self.user.is_staff = True
        self.user.save()

        recipient = VokoUserFactory.create()

        self._setup_session_with_user_ids([recipient.pk])

        response = self.client.get(reverse("admin_send_mail", kwargs={"pk": self.template.pk}))

        # Should redirect after sending
        self.assertEqual(response.status_code, 302)
        mock_mail_user.assert_called_once()
