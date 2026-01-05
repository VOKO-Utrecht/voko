# -*- coding: utf-8 -*-
from django.test import TestCase

from mailing.models import MailTemplate


class MailTemplateModelTest(TestCase):
    """Tests for the MailTemplate model."""

    def test_str_representation(self):
        """Test string representation of MailTemplate."""
        template = MailTemplate.objects.create(
            title="Welcome Email", subject="Welcome to VOKO", html_body="<p>Hello {{ user.first_name }}</p>"
        )
        self.assertEqual(str(template), "Welcome Email (Welcome to VOKO)")

    def test_default_subject(self):
        """Test default subject prefix."""
        template = MailTemplate.objects.create(title="Test", html_body="<p>Test</p>")
        self.assertEqual(template.subject, "VOKO Utrecht - ")

    def test_default_from_email(self):
        """Test default from_email is empty."""
        template = MailTemplate.objects.create(title="Test", html_body="<p>Test</p>")
        self.assertEqual(template.from_email, "")

    def test_html_body_stored(self):
        """Test HTML body is stored correctly."""
        html = "<h1>Title</h1><p>Content with <strong>bold</strong></p>"
        template = MailTemplate.objects.create(title="Test", html_body=html)
        self.assertEqual(template.html_body, html)

    def test_custom_from_email(self):
        """Test custom from email can be set."""
        template = MailTemplate.objects.create(
            title="Test", html_body="<p>Test</p>", from_email="custom@vokoutrecht.nl"
        )
        self.assertEqual(template.from_email, "custom@vokoutrecht.nl")
