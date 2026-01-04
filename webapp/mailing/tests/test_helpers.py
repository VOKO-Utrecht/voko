# -*- coding: utf-8 -*-
from unittest import mock

from django.test import TestCase, override_settings
from django.core import mail

from mailing.helpers import render_mail_template, get_template_by_id, mail_user
from mailing.models import MailTemplate
from accounts.tests.factories import VokoUserFactory


class RenderMailTemplateTest(TestCase):
    """Tests for the render_mail_template function."""

    def test_renders_subject(self):
        """Test subject is rendered with context."""
        template = MailTemplate.objects.create(
            title="Test",
            subject="Hello {{ user.first_name }}",
            html_body="<p>Body</p>"
        )
        user = VokoUserFactory.create(first_name="Jan")

        subject, html, plain, from_email = render_mail_template(template, user=user)

        self.assertEqual(subject, "Hello Jan")

    def test_renders_html_body(self):
        """Test HTML body is rendered with context."""
        template = MailTemplate.objects.create(
            title="Test",
            subject="Test",
            html_body="<p>Hello {{ user.first_name }} {{ user.last_name }}</p>"
        )
        user = VokoUserFactory.create(first_name="Jan", last_name="Janssen")

        subject, html, plain, from_email = render_mail_template(template, user=user)

        self.assertIn("Jan", html)
        self.assertIn("Janssen", html)
        self.assertIn("<p>", html)

    def test_renders_plain_text(self):
        """Test plain text is generated from HTML."""
        template = MailTemplate.objects.create(
            title="Test",
            subject="Test",
            html_body="<p>Hello <strong>World</strong></p>"
        )

        subject, html, plain, from_email = render_mail_template(template)

        # Plain text should not have HTML tags
        self.assertNotIn("<p>", plain)
        self.assertNotIn("<strong>", plain)
        self.assertIn("Hello", plain)
        self.assertIn("World", plain)

    def test_renders_from_email(self):
        """Test from_email is rendered."""
        template = MailTemplate.objects.create(
            title="Test",
            subject="Test",
            html_body="<p>Body</p>",
            from_email="noreply@vokoutrecht.nl"
        )

        subject, html, plain, from_email = render_mail_template(template)

        self.assertEqual(from_email, "noreply@vokoutrecht.nl")

    def test_renders_from_email_with_template_variable(self):
        """Test from_email can use template variables."""
        template = MailTemplate.objects.create(
            title="Test",
            subject="Test",
            html_body="<p>Body</p>",
            from_email="{{ user.email }}"
        )
        user = VokoUserFactory.create(email="user@example.com")

        subject, html, plain, from_email = render_mail_template(template, user=user)

        self.assertEqual(from_email, "user@example.com")


class GetTemplateByIdTest(TestCase):
    """Tests for the get_template_by_id function."""

    def test_returns_template(self):
        """Test returns template when found."""
        template = MailTemplate.objects.create(
            title="Test Template",
            html_body="<p>Test</p>"
        )

        result = get_template_by_id(template.id)

        self.assertEqual(result, template)

    @override_settings(DEBUG=True)
    def test_returns_placeholder_in_debug(self):
        """Test returns placeholder template in DEBUG mode when not found."""
        result = get_template_by_id(99999)

        self.assertIsNotNone(result)
        self.assertEqual(result.title, "TEST")

    @override_settings(DEBUG=False)
    def test_returns_none_in_production(self):
        """Test returns None in production when not found."""
        result = get_template_by_id(99999)

        self.assertIsNone(result)


class MailUserTest(TestCase):
    """Tests for the mail_user function."""

    @mock.patch('mailing.helpers.log')
    def test_sends_email(self, mock_log):
        """Test mail_user sends email."""
        user = VokoUserFactory.create(
            first_name="Jan",
            last_name="Janssen",
            email="jan@example.com"
        )

        mail_user(
            user,
            subject="Test Subject",
            html_body="<p>Test HTML</p>",
            plain_body="Test Plain",
            from_email="from@example.com"
        )

        # Check email was sent
        self.assertEqual(len(mail.outbox), 1)
        sent_mail = mail.outbox[0]
        self.assertEqual(sent_mail.subject, "Test Subject")
        self.assertIn("jan@example.com", sent_mail.to[0])

    @mock.patch('mailing.helpers.log')
    def test_logs_event(self, mock_log):
        """Test mail_user logs the event."""
        user = VokoUserFactory.create()

        mail_user(
            user,
            subject="Test Subject",
            html_body="<p>Test</p>",
            plain_body="Test",
            from_email=""
        )

        mock_log.log_event.assert_called_once()

    @mock.patch('mailing.helpers.log')
    @override_settings(DEFAULT_FROM_EMAIL="default@vokoutrecht.nl")
    def test_uses_default_from_email(self, mock_log):
        """Test uses DEFAULT_FROM_EMAIL when from_email is empty."""
        user = VokoUserFactory.create()

        mail_user(
            user,
            subject="Test Subject",
            html_body="<p>Test</p>",
            plain_body="Test",
            from_email=""
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].from_email, "default@vokoutrecht.nl")

    @mock.patch('mailing.helpers.log')
    def test_uses_custom_from_email(self, mock_log):
        """Test uses custom from_email when provided."""
        user = VokoUserFactory.create()

        mail_user(
            user,
            subject="Test Subject",
            html_body="<p>Test</p>",
            plain_body="Test",
            from_email="custom@vokoutrecht.nl"
        )

        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].from_email, "custom@vokoutrecht.nl")
