# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
import pytz

from vokou.testing import VokoTestCase
from news.models import Newsitem


class NewsitemsViewTest(VokoTestCase):
    """Tests for the NewsitemsView."""

    def test_requires_login(self):
        """Test view requires login."""
        response = self.client.get(reverse("view_newsitems"))
        self.assertEqual(response.status_code, 302)

    def test_logged_in_can_access(self):
        """Test logged in user can access."""
        self.login()
        response = self.client.get(reverse("view_newsitems"))
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        """Test uses correct template."""
        self.login()
        response = self.client.get(reverse("view_newsitems"))
        self.assertTemplateUsed(response, "news/newsitem_list.html")

    def test_shows_published_items(self):
        """Test published items appear in context."""
        self.login()
        now = datetime.now(pytz.utc)
        item = Newsitem.objects.create(
            title="Published News",
            publish=True,
            publish_date=now - timedelta(days=1)
        )

        response = self.client.get(reverse("view_newsitems"))
        self.assertIn(item, response.context["newsitems"])

    def test_hides_unpublished_items(self):
        """Test unpublished items do not appear."""
        self.login()
        item = Newsitem.objects.create(
            title="Unpublished News",
            publish=False
        )

        response = self.client.get(reverse("view_newsitems"))
        self.assertNotIn(item, response.context["newsitems"])

    def test_hides_future_published_items(self):
        """Test future-dated items do not appear."""
        self.login()
        future = datetime.now(pytz.utc) + timedelta(days=7)
        item = Newsitem.objects.create(
            title="Future News",
            publish=True,
            publish_date=future.date()
        )

        response = self.client.get(reverse("view_newsitems"))
        self.assertNotIn(item, response.context["newsitems"])

    def test_hides_old_items(self):
        """Test items older than 1 year do not appear."""
        self.login()
        old_date = datetime.now(pytz.utc) - timedelta(days=400)
        item = Newsitem.objects.create(
            title="Old News",
            publish=True,
            publish_date=old_date.date()
        )

        response = self.client.get(reverse("view_newsitems"))
        self.assertNotIn(item, response.context["newsitems"])

    def test_items_ordered_by_publish_date_descending(self):
        """Test items are ordered newest first."""
        self.login()
        now = datetime.now(pytz.utc)

        old_item = Newsitem.objects.create(
            title="Older News",
            publish=True,
            publish_date=(now - timedelta(days=30)).date()
        )
        new_item = Newsitem.objects.create(
            title="Newer News",
            publish=True,
            publish_date=(now - timedelta(days=1)).date()
        )

        response = self.client.get(reverse("view_newsitems"))
        items = list(response.context["newsitems"])

        self.assertEqual(items[0], new_item)
        self.assertEqual(items[1], old_item)

    def test_view_single_newsitem(self):
        """Test viewing a specific newsitem by pk."""
        self.login()
        now = datetime.now(pytz.utc)
        item = Newsitem.objects.create(
            title="Specific News",
            publish=True,
            publish_date=(now - timedelta(days=1)).date()
        )

        response = self.client.get(
            reverse("view_newsitem", kwargs={"pk": item.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["newsitem"], item)

    def test_view_nonexistent_newsitem(self):
        """Test viewing non-existent newsitem shows first published."""
        self.login()
        now = datetime.now(pytz.utc)
        existing = Newsitem.objects.create(
            title="Existing News",
            publish=True,
            publish_date=(now - timedelta(days=1)).date()
        )

        response = self.client.get(
            reverse("view_newsitem", kwargs={"pk": 99999})
        )
        self.assertEqual(response.status_code, 200)
        # Should fall back to first item
        self.assertIn("newsitem", response.context)
