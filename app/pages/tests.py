from django.test import SimpleTestCase
from django.urls import resolve, reverse

from pages.views import HomePageView


class HomepageTests(SimpleTestCase):
    def setUp(self):
        url = reverse("home")
        self.response = self.client.get(url)
        self.view = resolve("/")

    def test_url_exists_at_correct_location(self):
        self.assertEqual(self.response.status_code, 200)

    def test_homepage_template(self):
        self.assertTemplateUsed(self.response, "home.html")

    def test_homepage_contains_correct_html(self):
        self.assertContains(self.response, "home")

    def test_homepage_does_not_contain_incorrect_html(self):
        self.assertNotContains(self.response, "Wrong text.")

    def test_homepage_url_resolves_homepage_view(self):
        self.assertEqual(self.view.func.__name__, HomePageView.as_view().__name__)
