from django.test import SimpleTestCase
from django.urls import resolve, reverse

from pages.views import AboutPageView, HomePageView


class HomepageTests(SimpleTestCase):
    view_class = HomePageView
    template = "home.html"
    template_name = "home"
    text_in_html = "home"
    text_not_in_html = "wrong text"

    def setUp(self):
        url = reverse(self.template_name)
        self.response = self.client.get(url)
        self.view = resolve("/")

    def test_page_and_template(self):
        # test url exists at correct location
        self.assertEqual(self.response.status_code, 200)
        # test url resolves correct view
        self.assertEqual(self.view.func.__name__, self.view_class.as_view().__name__)
        # test correct template is used
        self.assertTemplateUsed(self.response, self.template)
        # test HTML content
        self.assertContains(self.response, self.text_in_html)
        self.assertNotContains(self.response, self.text_not_in_html)


class AboutPageTests(SimpleTestCase):
    view_class = AboutPageView
    template = "about.html"
    template_name = "about"
    text_in_html = "about"
    text_not_in_html = "wrong text"

    def setUp(self):
        url = reverse(self.template_name)
        self.response = self.client.get(url)
        self.view = resolve("/")

    def test_page_and_template(self):
        # test url exists at correct location
        self.assertEqual(self.response.status_code, 200)
        # test url resolves correct view
        self.assertEqual(self.view.func.__name__, self.view_class.as_view().__name__)
        # test correct template is used
        self.assertTemplateUsed(self.response, self.template)
        # test HTML content
        self.assertContains(self.response, self.text_in_html)
        self.assertNotContains(self.response, self.text_not_in_html)
