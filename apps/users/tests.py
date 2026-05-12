from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.users.models import HouseManager


class UserModelTests(TestCase):
    def test_save_normalizes_phone_number(self):
        user = get_user_model().objects.create(
            username="tenant",
            phone="0712345678",
        )

        self.assertEqual(user.phone, "254712345678")

    def test_name_combines_first_and_last_name(self):
        user = get_user_model().objects.create(
            username="owner",
            first_name="Grace",
            last_name="Hopper",
        )

        self.assertEqual(user.name(), "Grace Hopper")

    def test_string_representation_uses_username(self):
        user = get_user_model().objects.create(username="owner")

        self.assertEqual(str(user), "owner")

    def test_status_reflects_active_flag(self):
        active_user = get_user_model().objects.create(username="active", is_active=True)
        inactive_user = get_user_model().objects.create(
            username="inactive", is_active=False
        )

        self.assertEqual(active_user.status(), "Active")
        self.assertEqual(inactive_user.status(), "Inactive")


class HouseManagerModelTests(TestCase):
    def test_string_representation_uses_name(self):
        manager = HouseManager.objects.create(name="Care Manager")

        self.assertEqual(str(manager), "Care Manager")


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class UserViewTests(TestCase):
    def test_login_page_is_public(self):
        response = self.client.get(reverse("login"))

        self.assertEqual(response.status_code, 200)

    def test_logout_requires_login(self):
        response = self.client.get(reverse("logout"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/users/login/", response["Location"])
