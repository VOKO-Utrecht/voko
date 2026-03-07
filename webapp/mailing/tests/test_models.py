# -*- coding: utf-8 -*-
from django.test import TestCase

from mailing.models import MailTemplate, MailTemplateTag


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

    def test_is_active_default_true(self):
        """Test that is_active defaults to True."""
        template = MailTemplate.objects.create(title="Test", html_body="<p>Test</p>")
        self.assertTrue(template.is_active)

    def test_is_active_can_be_set_false(self):
        """Test that templates can be marked inactive."""
        template = MailTemplate.objects.create(title="Test", html_body="<p>Test</p>", is_active=False)
        self.assertFalse(template.is_active)

    def test_tags_can_be_added(self):
        """Test that tags can be associated with a template."""
        tag = MailTemplateTag.objects.create(name="welkom")
        template = MailTemplate.objects.create(title="Test", html_body="<p>Test</p>")
        template.tags.add(tag)
        self.assertIn(tag, template.tags.all())

    def test_tags_default_empty(self):
        """Test that templates have no tags by default."""
        template = MailTemplate.objects.create(title="Test", html_body="<p>Test</p>")
        self.assertEqual(template.tags.count(), 0)

    def test_tag_str(self):
        tag = MailTemplateTag.objects.create(name="bestel")
        self.assertEqual(str(tag), "bestel")
