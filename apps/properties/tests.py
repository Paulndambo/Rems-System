from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.core.constants import MaintenanceStatuses
from apps.core.models import Month, Year
from apps.payments.models import UnitMonthBill
from apps.properties.models import (
    ElectricityBill,
    GarbageBill,
    MaintenanceRequest,
    Property,
    PropertyUnit,
    WaterBill,
)
from apps.properties.water_bills.billing_mixin import TenantBillingMixin
from apps.tenants.models import Tenant


class PropertyTestCase(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create(username="owner")
        self.property = Property.objects.create(
            owner=self.owner,
            name="Sunrise Apartments",
            city="Nairobi",
            country="Kenya",
            units=3,
        )

    def create_unit(self, name, rent, is_occupied=False, unit_type="Bedsitter"):
        return PropertyUnit.objects.create(
            property=self.property,
            name=name,
            rent=Decimal(rent),
            is_occupied=is_occupied,
            unit_type=unit_type,
        )


class PropertyModelTests(PropertyTestCase):
    def test_property_summary_methods_count_related_units(self):
        self.create_unit("A1", "10000.00", is_occupied=True)
        self.create_unit("A2", "12000.00", is_occupied=False)
        self.create_unit("A3", "8000.00", is_occupied=False, unit_type="Maintenance")

        self.assertEqual(str(self.property), "Sunrise Apartments")
        self.assertEqual(self.property.status(), "Inactive")
        self.assertEqual(self.property.total_units(), 3)
        self.assertEqual(self.property.occupied_units(), 1)
        self.assertEqual(self.property.vacant_units(), 2)
        self.assertEqual(self.property.maintenance_units(), 1)
        self.assertEqual(self.property.occupancy_rate(), 33.33)
        self.assertEqual(self.property.monthly_revenue(), Decimal("10000.00"))

    def test_occupancy_rate_is_zero_without_units(self):
        self.assertEqual(self.property.occupancy_rate(), 0)


class PropertyUnitModelTests(PropertyTestCase):
    def test_string_representation_uses_unit_name(self):
        unit = self.create_unit("A1", "10000.00")

        self.assertEqual(str(unit), "A1")


class MaintenanceRequestModelTests(PropertyTestCase):
    def test_string_representation_uses_title(self):
        request = MaintenanceRequest.objects.create(
            title="Leaking sink",
            property=self.property,
            description="Kitchen sink is leaking",
        )

        self.assertEqual(str(request), "Leaking sink")


class UtilityBillModelTests(PropertyTestCase):
    def setUp(self):
        super().setUp()
        tenant_user = get_user_model().objects.create(username="tenant")
        self.tenant = Tenant.objects.create(user=tenant_user)
        self.unit = PropertyUnit.objects.create(
            property=self.property,
            name="A1",
            rent=Decimal("10000.00"),
            water_price=Decimal("250.00"),
            tenant=self.tenant,
        )
        self.year = Year.objects.create(name="2026")
        self.month = Month.objects.create(name="January", year=self.year)

    def test_water_bill_save_sets_tenant_and_dates_from_month_and_year(self):
        bill = WaterBill.objects.create(
            property=self.property,
            unit=self.unit,
            month=self.month,
            year=self.year,
            previous_reading=Decimal("10.00"),
            current_reading=Decimal("15.00"),
        )

        self.assertEqual(bill.tenant, self.tenant)
        self.assertEqual(bill.reading_date, date(2026, 2, 1))
        self.assertEqual(bill.due_date, date(2026, 2, 5))

    def test_water_bill_total_amount_includes_previous_balance_and_rounds_up(self):
        bill = WaterBill(
            property=self.property,
            unit=self.unit,
            units_consumed=Decimal("3.25"),
            previous_balance=Decimal("10.10"),
        )

        self.assertEqual(bill.total_amount(), 823)

    def test_water_bill_refresh_bill_updates_linked_unit_month_bill(self):
        unit_bill = UnitMonthBill.objects.create(
            unit=self.unit,
            tenant=self.tenant,
            month=self.month,
            year=self.year,
            rent_amount=Decimal("10000.00"),
        )
        bill = WaterBill.objects.create(
            unit_bill=unit_bill,
            property=self.property,
            unit=self.unit,
            previous_reading=Decimal("20.00"),
            current_reading=Decimal("25.50"),
        )

        bill.refresh_bill()
        unit_bill.refresh_from_db()
        bill.refresh_from_db()

        self.assertEqual(bill.units_consumed, Decimal("5.5000"))
        self.assertEqual(bill.amount, Decimal("1375.00"))
        self.assertEqual(unit_bill.water_amount, Decimal("1375.00"))
        self.assertEqual(unit_bill.amount_expected, Decimal("11375.00"))

    def test_water_bill_balance_subtracts_amount_paid(self):
        bill = WaterBill.objects.create(
            property=self.property,
            unit=self.unit,
            amount=Decimal("500.00"),
            amount_paid=Decimal("125.50"),
        )

        self.assertEqual(bill.balance(), Decimal("374.50"))

    def test_garbage_and_electricity_bill_strings_and_balances(self):
        garbage_bill = GarbageBill.objects.create(
            property=self.property,
            unit=self.unit,
            amount=Decimal("130.00"),
            amount_paid=Decimal("30.00"),
        )
        electricity_bill = ElectricityBill.objects.create(
            property=self.property,
            unit=self.unit,
            amount=Decimal("900.00"),
            amount_paid=Decimal("250.00"),
            status=MaintenanceStatuses.PENDING.value,
        )

        self.assertEqual(str(garbage_bill), "A1")
        self.assertEqual(str(electricity_bill), "A1")
        self.assertEqual(electricity_bill.balance(), Decimal("650.00"))


class TenantBillingMixinTests(PropertyTestCase):
    def setUp(self):
        super().setUp()
        tenant_user = get_user_model().objects.create(username="billing-tenant")
        self.tenant = Tenant.objects.create(user=tenant_user)
        self.unit = PropertyUnit.objects.create(
            property=self.property,
            name="B1",
            rent=Decimal("12000.00"),
            water_price=Decimal("250.00"),
            water_meter_number="WM-001",
            tenant=self.tenant,
        )
        self.year = Year.objects.create(name="2026")
        self.month = Month.objects.create(name="May", year=self.year)

    def test_generate_bill_creates_unit_water_and_rent_bills(self):
        result = TenantBillingMixin(
            year=self.year,
            month=self.month,
            previous_reading=10,
            current_reading=14.5,
            unit=self.unit,
        ).generate_bill()

        unit_bill = UnitMonthBill.objects.get(unit=self.unit)
        water_bill = WaterBill.objects.get(unit=self.unit)

        self.assertTrue(result)
        self.assertEqual(unit_bill.tenant, self.tenant)
        self.assertEqual(unit_bill.rent_amount, Decimal("12000.00"))
        self.assertEqual(unit_bill.water_amount, Decimal("1125.00"))
        self.assertEqual(unit_bill.amount_expected, Decimal("13125.00"))
        self.assertEqual(water_bill.meter_number, "WM-001")
        self.assertEqual(water_bill.units_consumed, Decimal("4.5000"))

    def test_generate_bill_updates_existing_unit_bill(self):
        existing_bill = UnitMonthBill.objects.create(
            unit=self.unit,
            tenant=self.tenant,
            month=self.month,
            year=self.year,
            rent_amount=Decimal("1.00"),
            water_amount=Decimal("1.00"),
        )

        TenantBillingMixin(
            year=self.year,
            month=self.month,
            previous_reading=20,
            current_reading=22,
            unit=self.unit,
        ).generate_bill()

        existing_bill.refresh_from_db()
        self.assertEqual(existing_bill.rent_amount, Decimal("12000.00"))
        self.assertEqual(existing_bill.water_amount, Decimal("500.00"))
        self.assertEqual(existing_bill.amount_expected, Decimal("12500.00"))


class PropertyViewTests(TestCase):
    def test_property_routes_require_login(self):
        protected_routes = [
            reverse("properties"),
            reverse("new-property"),
            reverse("units"),
        ]

        for route in protected_routes:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 302)
                self.assertIn("/users/login/", response["Location"])

    def test_get_units_by_property_returns_json_for_missing_property(self):
        response = self.client.get(reverse("get-units-by-property"), {"property_id": 999})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"units": []})
