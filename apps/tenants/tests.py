from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.properties.models import Property, PropertyUnit
from apps.payments.models import GarbageBill, SecurityDeposit, TenantPayment, UnitMonthBill
from apps.properties.models import WaterBill
from apps.tenants.new_tenant_mixin import OnboardTenantMixin, clean_up_unit
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


class OnboardTenantMixinTests(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create(username="owner")
        self.property = Property.objects.create(
            owner=self.owner,
            name="Sunrise Apartments",
            city="Nairobi",
            country="Kenya",
            units=1,
        )
        self.unit = PropertyUnit.objects.create(
            property=self.property,
            name="A1",
            rent=Decimal("15000.00"),
            security_deposit=Decimal("15000.00"),
        )

    def test_run_creates_tenant_user_assigns_unit_and_security_deposit(self):
        OnboardTenantMixin(
            first_name="New",
            last_name="Tenant",
            email="",
            phone="0712345678",
            id_number="12345678",
            gender="Female",
            move_in_date=date(2026, 5, 13),
            lease_duration="1 Year",
            lease_date=date(2026, 5, 13),
            marital_status="Single",
            rental_unit=self.unit.id,
            occupation="Engineer",
        ).run()

        self.unit.refresh_from_db()
        tenant = Tenant.objects.get(user__username="New.Tenant")

        self.assertEqual(tenant.user.email, "New.Tenant@gmail.com")
        self.assertEqual(tenant.user.phone, "254712345678")
        self.assertEqual(tenant.renews_every, "1 Year")
        self.assertEqual(self.unit.tenant, tenant)
        self.assertTrue(self.unit.is_occupied)
        self.assertTrue(
            SecurityDeposit.objects.filter(
                tenant=tenant,
                unit=self.unit,
                amount_expected=Decimal("15000.00"),
            ).exists()
        )

    def test_clean_up_unit_detaches_related_billing_records(self):
        tenant_user = get_user_model().objects.create(username="existing")
        tenant = Tenant.objects.create(user=tenant_user)
        self.unit.tenant = tenant
        self.unit.save()
        WaterBill.objects.create(property=self.property, unit=self.unit, tenant=tenant)
        UnitMonthBill.objects.create(unit=self.unit, tenant=tenant)
        TenantPayment.objects.create(
            tenant=tenant,
            unit=self.unit,
            amount_paid=Decimal("100.00"),
            payment_date=date(2026, 5, 13),
        )
        GarbageBill.objects.create(
            unit=self.unit,
            tenant=tenant,
            amount_expected=Decimal("130.00"),
        )

        clean_up_unit(self.unit)

        self.assertIsNone(WaterBill.objects.get().unit)
        self.assertIsNone(UnitMonthBill.objects.get().unit)
        self.assertIsNone(TenantPayment.objects.get().unit)
        self.assertIsNone(GarbageBill.objects.get().unit)
