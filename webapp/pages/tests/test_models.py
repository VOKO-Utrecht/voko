# -*- coding: utf-8 -*-
from django.test import TestCase

from pages.models import Page


class PageModelTest(TestCase):
    def test_str_representation(self):
        page = Page.objects.create(title="Over ons", slug="over-ons")
        self.assertEqual(str(page), "Over ons")

    def test_slug_auto_generated_from_title(self):
        page = Page.objects.create(title="Over ons")
        self.assertEqual(page.slug, "over-ons")

    def test_explicit_slug_is_preserved(self):
        page = Page.objects.create(title="Over ons", slug="custom-slug")
        self.assertEqual(page.slug, "custom-slug")

    def test_default_published_is_false(self):
        page = Page.objects.create(title="Test", slug="test")
        self.assertFalse(page.published)

    def test_can_store_html_content(self):
        html = "<h1>Heading</h1><p>Body text</p>"
        page = Page.objects.create(title="Test", slug="test", content=html)
        self.assertEqual(page.content, html)

    def test_slug_unique(self):
        Page.objects.create(title="Test", slug="test")
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Page.objects.create(title="Test 2", slug="test")

    def test_timestamps_are_set(self):
        page = Page.objects.create(title="Test", slug="test")
        self.assertIsNotNone(page.created)
        self.assertIsNotNone(page.modified)
