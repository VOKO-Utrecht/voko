# -*- coding: utf-8 -*-
from django.urls import reverse

from vokou.testing import VokoTestCase
from pages.models import Page


class PageDetailViewTest(VokoTestCase):
    def setUp(self):
        self.page = Page.objects.create(
            title="Statuten",
            slug="statuten",
            content="<p>Onze statuten.</p>",
            published=True,
        )

    def test_requires_login(self):
        response = self.client.get(reverse("pages.page_detail", kwargs={"slug": "statuten"}))
        self.assertEqual(response.status_code, 302)

    def test_logged_in_can_view_published_page(self):
        self.login()
        response = self.client.get(reverse("pages.page_detail", kwargs={"slug": "statuten"}))
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        self.login()
        response = self.client.get(reverse("pages.page_detail", kwargs={"slug": "statuten"}))
        self.assertTemplateUsed(response, "pages/page_detail.html")

    def test_page_in_context(self):
        self.login()
        response = self.client.get(reverse("pages.page_detail", kwargs={"slug": "statuten"}))
        self.assertEqual(response.context["page"], self.page)

    def test_unpublished_page_returns_404(self):
        Page.objects.create(title="Draft", slug="draft", published=False)
        self.login()
        response = self.client.get(reverse("pages.page_detail", kwargs={"slug": "draft"}))
        self.assertEqual(response.status_code, 404)

    def test_nonexistent_page_returns_404(self):
        self.login()
        response = self.client.get(reverse("pages.page_detail", kwargs={"slug": "does-not-exist"}))
        self.assertEqual(response.status_code, 404)
