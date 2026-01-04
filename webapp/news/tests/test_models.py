# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from django.test import TestCase
from django.utils import timezone
import pytz

from news.models import Newsitem


class NewsitemModelTest(TestCase):
    """Tests for the Newsitem model."""

    def test_str_representation(self):
        """Test string representation of Newsitem."""
        item = Newsitem.objects.create(
            title="Test News Article"
        )
        self.assertEqual(str(item), "Test News Article")

    def test_default_publish_is_false(self):
        """Test default publish value is False."""
        item = Newsitem.objects.create(title="Test")
        self.assertFalse(item.publish)

    def test_default_publish_date_is_none(self):
        """Test default publish_date is None."""
        item = Newsitem.objects.create(title="Test")
        self.assertIsNone(item.publish_date)

    def test_publish_date_set_on_first_publish(self):
        """Test publish_date is set when publish is changed to True."""
        item = Newsitem.objects.create(title="Test", publish=False)
        self.assertIsNone(item.publish_date)

        # Now publish
        item.publish = True
        item.save()

        self.assertIsNotNone(item.publish_date)

    def test_publish_date_not_updated_on_subsequent_saves(self):
        """Test publish_date is not changed on subsequent saves."""
        item = Newsitem.objects.create(title="Test", publish=True)
        original_date = item.publish_date

        # Save again
        item.title = "Updated Title"
        item.save()

        # Refresh from DB
        item.refresh_from_db()
        self.assertEqual(item.publish_date, original_date)

    def test_can_store_html_content(self):
        """Test HTML content can be stored."""
        html = "<h1>Title</h1><p>Paragraph with <strong>bold</strong></p>"
        item = Newsitem.objects.create(
            title="Test",
            content=html
        )
        self.assertEqual(item.content, html)

    def test_can_store_summary(self):
        """Test summary field stores data."""
        item = Newsitem.objects.create(
            title="Test",
            summary="This is a short summary"
        )
        self.assertEqual(item.summary, "This is a short summary")

    def test_summary_can_be_blank(self):
        """Test summary can be blank."""
        item = Newsitem.objects.create(title="Test", summary="")
        self.assertEqual(item.summary, "")

    def test_summary_can_be_null(self):
        """Test summary can be null."""
        item = Newsitem.objects.create(title="Test")
        self.assertIsNone(item.summary)

    def test_org_publish_tracks_original_value(self):
        """Test org_publish tracks initial publish value."""
        item = Newsitem.objects.create(title="Test", publish=True)

        # Re-fetch from database
        item = Newsitem.objects.get(pk=item.pk)

        # org_publish should be True now
        self.assertTrue(item.org_publish)

    def test_timestamps_are_set(self):
        """Test created and modified timestamps are set."""
        item = Newsitem.objects.create(title="Test")
        self.assertIsNotNone(item.created)
        self.assertIsNotNone(item.modified)
