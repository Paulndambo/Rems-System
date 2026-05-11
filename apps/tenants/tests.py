from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.properties.models import Property, PropertyUnit
from apps.tenants.models import Tenant, TenantNextOfKin


class TenantModelTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create(username="tenant")
        self.tenant = Tenant.objects.create(
            user=self.user,
            lease_date=date(2026, 1, 1),
            move_in_date=date(2026, 1, 3),
        )

    def test_string_representation_uses_username(self):
        self.assertEqual(str(self.tenant), "tenant")

    def test_lease_end_date_uses_configured_duration(self):
        cases = [
            ("3 Months", date(2026, 4, 1)),
            ("6 Months", date(2026, 6, 30)),
            ("9 Months", date(2026, 9, 28)),
            ("1 Year", date(2027, 1, 1)),
            ("Unexpected", date(2027, 1, 1)),
        ]

        for duration, expected_end_date in cases:
            with self.subTest(duration=duration):
                self.tenant.lease_duration = duration
                self.assertEqual(self.tenant.lease_end_date(), expected_end_date)

    def test_lease_end_date_is_none_without_lease_date(self):
        self.tenant.lease_date = None

        self.assertIsNone(self.tenant.lease_end_date())

    def test_unit_returns_property_unit_assigned_to_tenant(self):
        owner = get_user_model().objects.create(username="owner")
        property_ = Property.objects.create(
            owner=owner,
            name="Sunrise Apartments",
            city="Nairobi",
            country="Kenya",
            units=1,
        )
        unit = PropertyUnit.objects.create(
            property=property_,
            name="A1",
            rent=Decimal("15000.00"),
            tenant=self.tenant,
        )

        self.assertEqual(self.tenant.unit(), unit)


class TenantNextOfKinModelTests(TestCase):
    def test_string_representation_uses_name(self):
        user = get_user_model().objects.create(username="tenant-kin")
        tenant = Tenant.objects.create(user=user)
        next_of_kin = TenantNextOfKin.objects.create(
            tenant=tenant,
            name="Jane Doe",
            phone="254700000000",
            email="jane@example.com",
            relationship="Sister",
        )

        self.assertEqual(str(next_of_kin), "Jane Doe")


class TenantViewTests(TestCase):
    def test_tenant_list_requires_login(self):
        response = self.client.get(reverse("tenants"))

        self.assertEqual(response.status_code, 302)
        self.assertIn("/users/login/", response["Location"])
