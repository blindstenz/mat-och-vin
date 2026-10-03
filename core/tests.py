import json

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse


class PwaTests(TestCase):
    def test_manifest(self):
        response = self.client.get(reverse("manifest"))
        self.assertEqual(response["Content-Type"], "application/manifest+json")
        data = json.loads(response.content)
        self.assertEqual(data["lang"], "sv")
        self.assertEqual(data["display"], "standalone")
        self.assertEqual(data["start_url"], reverse("recipes:list"))
        self.assertEqual({icon["sizes"] for icon in data["icons"]}, {"192x192", "512x512"})

    def test_service_worker_served_from_root(self):
        response = self.client.get("/sw.js")
        self.assertEqual(response["Content-Type"], "application/javascript")
        self.assertContains(response, "/offline/")
        self.assertContains(response, "pico.red.min.css")

    def test_offline_page_is_public(self):
        response = self.client.get(reverse("offline"))
        self.assertContains(response, "Ingen anslutning")


class AuthTests(TestCase):
    def test_home_redirects_anonymous_to_login(self):
        self.assertRedirects(self.client.get("/"), reverse("login"))

    def test_home_redirects_user_to_recipes(self):
        self.client.force_login(get_user_model().objects.create_user("bjorn"))
        self.assertRedirects(self.client.get("/"), reverse("recipes:list"))

    def test_login_page_is_swedish(self):
        response = self.client.get(reverse("login"))
        self.assertContains(response, "Logga in")
        self.assertContains(response, "Användarnamn")

    def test_signup_closed_by_default(self):
        self.assertEqual(self.client.get(reverse("signup")).status_code, 404)

    @override_settings(ALLOW_SIGNUP=True)
    def test_signup_when_enabled(self):
        response = self.client.post(
            reverse("signup"),
            {"username": "anna", "password1": "ett-langt-losen-42", "password2": "ett-langt-losen-42"},
        )
        self.assertRedirects(response, reverse("recipes:list"))
        self.assertTrue(get_user_model().objects.filter(username="anna").exists())
