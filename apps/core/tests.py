from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from apps.core.clean_phone_number import clean_phone_number
from apps.core.constants import MonthsNames, PaymentStatuses, UserRoles
from apps.core.due_date_normalizer import get_due_date
from apps.core.models import Month, UserAction, WaterPrice, Year


class CleanPhoneNumberTests(TestCase):
    def test_removes_plus_from_international_number(self):
        self.assertEqual(clean_phone_number("+254712345678"), "254712345678")

    def test_converts_local_zero_prefix_to_kenyan_country_code(self):
        self.assertEqual(clean_phone_number("0712345678"), "254712345678")

    def test_leaves_already_normalized_number_unchanged(self):
        self.assertEqual(clean_phone_number("254712345678"), "254712345678")


class DueDateNormalizerTests(TestCase):
    def test_returns_fifth_day_for_named_month_and_year(self):
        self.assertEqual(get_due_date("march", 2026), date(2026, 3, 5))

    def test_rejects_invalid_month_name(self):
        with self.assertRaises(ValueError):
            get_due_date("not-a-month", 2026)


class ConstantsTests(TestCase):
    def test_enum_choices_use_value_as_database_value(self):
        self.assertIn(("January", "JANUARY"), MonthsNames.choices())
        self.assertIn(("Paid", "PAID"), PaymentStatuses.choices())
        self.assertIn(("Landlord", "LANDLORD"), UserRoles.choices())


class CoreModelTests(TestCase):
    def test_core_model_string_representations(self):
        year = Year.objects.create(name="2026")
        month = Month.objects.create(name="May", year=year)
        water_price = WaterPrice.objects.create(unit_price=Decimal("250.00"))

        self.assertEqual(str(year), f"2026-({year.id})")
        self.assertEqual(str(month), "May")
        self.assertEqual(str(water_price), "Ksh 250.00")

    def test_user_action_string_includes_actor_and_action(self):
        user = get_user_model().objects.create(username="landlord", first_name="Ada")
        action = UserAction.objects.create(user=user, action="Created property")

        self.assertEqual(str(action), "landlord - Created property")


@override_settings(
    STORAGES={
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }
)
class CoreViewTests(TestCase):
    def test_landing_page_is_public(self):
        response = self.client.get(reverse("landing-page"))

        self.assertEqual(response.status_code, 200)

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/users/login/", response["Location"])

    def test_chart_data_api_is_public_json_endpoint(self):
        response = self.client.get(reverse("chart_data_api"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")
