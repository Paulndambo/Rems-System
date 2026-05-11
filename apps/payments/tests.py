from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.core.constants import PaymentStatuses
from apps.core.models import Month, Year
from apps.payments.models import (
    GarbageBill,
    RentBill,
    SecurityDeposit,
    TemporaryMonthBill,
    TenantPayment,
    UnitMonthBill,
    WaterBillPayment,
    RentPayment,
)
from apps.payments.unit_bills.payment_processor import ProcessTenantPayment
from apps.properties.models import Property, PropertyUnit, WaterBill
from apps.tenants.models import Tenant


class BillingTestCase(TestCase):
    def setUp(self):
        self.owner = get_user_model().objects.create(username="owner")
        self.tenant_user = get_user_model().objects.create(
            username="tenant",
            first_name="Test",
            last_name="Tenant",
            phone="0712345678",
        )
        self.tenant = Tenant.objects.create(user=self.tenant_user)
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
            rent=Decimal("10000.00"),
            tenant=self.tenant,
            water_price=Decimal("250.00"),
        )
        self.year = Year.objects.create(name="2026")
        self.month = Month.objects.create(name="May", year=self.year)


class UnitMonthBillModelTests(BillingTestCase):
    def test_update_amount_expected_uses_rent_and_water(self):
        bill = UnitMonthBill.objects.create(
            unit=self.unit,
            tenant=self.tenant,
            rent_amount=Decimal("10000.00"),
            water_amount=Decimal("1250.00"),
            garbage_amount=Decimal("130.00"),
        )

        bill.update_amount_expected()

        self.assertEqual(bill.amount_expected, Decimal("11250.00"))

    def test_unit_bill_receipt_link_uses_configured_backend_url(self):
        bill = UnitMonthBill.objects.create(unit=self.unit, tenant=self.tenant)

        self.assertEqual(
            bill.unit_bill_receipt_link(),
            f"http://localhost:8000/payments/unit-bill-receipt/{bill.id}/",
        )

    def test_balance_helpers_and_status_text(self):
        bill = UnitMonthBill.objects.create(
            unit=self.unit,
            tenant=self.tenant,
            rent_amount=Decimal("10000.00"),
            rent_amount_paid=Decimal("3000.00"),
            water_amount=Decimal("1250.00"),
            water_amount_paid=Decimal("1250.00"),
            amount_expected=Decimal("11250.00"),
            amount_paid=Decimal("4250.00"),
        )

        self.assertEqual(bill.balance(), Decimal("7000.00"))
        self.assertEqual(bill.rent_balance(), Decimal("7000.00"))
        self.assertEqual(bill.water_balance(), Decimal("0.00"))
        self.assertFalse(bill.rent_fully_paid())
        self.assertTrue(bill.water_fully_paid())
        self.assertEqual(bill.unit_bill_status(), "Pending")

    def test_disclaimer_reports_missing_water_before_missing_rent(self):
        bill = UnitMonthBill.objects.create(
            unit=self.unit,
            tenant=self.tenant,
            rent_amount=Decimal("0.00"),
            water_amount=Decimal("0.00"),
        )

        self.assertEqual(bill.bill_disclaimer(), "Water bill is missing")

        bill.water_amount = Decimal("100.00")
        self.assertEqual(bill.bill_disclaimer(), "Rent bill is missing")

    def test_mark_as_paid_sets_amounts_and_status(self):
        bill = UnitMonthBill.objects.create(
            unit=self.unit,
            tenant=self.tenant,
            rent_amount=Decimal("10000.00"),
            water_amount=Decimal("1250.00"),
            amount_expected=Decimal("11250.00"),
        )

        bill.mark_as_paid()

        self.assertEqual(bill.status, PaymentStatuses.PAID.value)
        self.assertTrue(bill.fully_paid)
        self.assertEqual(bill.amount_paid, Decimal("11250.00"))
        self.assertEqual(bill.rent_amount_paid, Decimal("10000.00"))
        self.assertEqual(bill.water_amount_paid, Decimal("1250.00"))


class OtherPaymentModelTests(BillingTestCase):
    def test_rent_garbage_and_security_deposit_balances(self):
        rent_bill = RentBill.objects.create(
            tenant=self.tenant,
            unit=self.unit,
            amount_expected=Decimal("10000.00"),
            amount_paid=Decimal("4000.00"),
            due_date=date(2026, 5, 5),
        )
        garbage_bill = GarbageBill.objects.create(
            unit=self.unit,
            tenant=self.tenant,
            amount_expected=Decimal("130.00"),
            amount_paid=Decimal("30.00"),
        )
        deposit = SecurityDeposit.objects.create(
            unit=self.unit,
            tenant=self.tenant,
            amount_expected=Decimal("10000.00"),
            amount_paid=Decimal("2500.00"),
        )

        self.assertEqual(rent_bill.balance(), Decimal("6000.00"))
        self.assertEqual(garbage_bill.balance(), Decimal("100.00"))
        self.assertEqual(deposit.balance(), Decimal("7500.00"))
        self.assertEqual(str(deposit), "Test Tenant")

    def test_temporary_month_bill_calculates_water_and_total(self):
        temporary_bill = TemporaryMonthBill.objects.create(
            unit=self.unit,
            month=self.month,
            year=self.year,
            rent_amount=Decimal("10000.00"),
            previous_reading=Decimal("10.00"),
            current_reading=Decimal("14.50"),
        )

        self.assertEqual(str(temporary_bill), "A1 - May 2026")
        self.assertEqual(temporary_bill.consumption(), Decimal("4.50"))
        self.assertEqual(temporary_bill.water_amount(), Decimal("1125.00"))
        self.assertEqual(temporary_bill.total(), Decimal("11125.00"))

    def test_temporary_month_bill_returns_zero_without_current_reading(self):
        temporary_bill = TemporaryMonthBill.objects.create(
            unit=self.unit,
            month=self.month,
            year=self.year,
            previous_reading=Decimal("10.00"),
            current_reading=Decimal("0.00"),
        )

        self.assertEqual(temporary_bill.consumption(), Decimal("0.00"))
        self.assertEqual(temporary_bill.water_amount(), Decimal("0.00"))


class ProcessTenantPaymentTests(BillingTestCase):
    def create_monthly_bill(self):
        unit_bill = UnitMonthBill.objects.create(
            unit=self.unit,
            tenant=self.tenant,
            month=self.month,
            year=self.year,
            rent_amount=Decimal("10000.00"),
            water_amount=Decimal("1250.00"),
            amount_expected=Decimal("11250.00"),
        )
        RentBill.objects.create(
            unit_bill=unit_bill,
            tenant=self.tenant,
            unit=self.unit,
            amount_expected=Decimal("10000.00"),
            due_date=date(2026, 5, 5),
            month=self.month,
            year=self.year,
        )
        WaterBill.objects.create(
            unit_bill=unit_bill,
            property=self.property,
            unit=self.unit,
            tenant=self.tenant,
            amount=Decimal("1250.00"),
            month=self.month,
            year=self.year,
        )
        return unit_bill

    def test_processing_partial_rent_and_water_payment_records_all_ledgers(self):
        unit_bill = self.create_monthly_bill()

        ProcessTenantPayment(
            unit_bill=unit_bill,
            rent_amount=5000,
            water_amount=500,
            payment_method="Cash",
            payment_date=date(2026, 5, 12),
            reference_number="RCPT-001",
        ).run()

        unit_bill.refresh_from_db()
        rent_bill = RentBill.objects.get(unit_bill=unit_bill)
        water_bill = WaterBill.objects.get(unit_bill=unit_bill)
        tenant_payment = TenantPayment.objects.get(reference="RCPT-001")

        self.assertEqual(unit_bill.amount_paid, Decimal("5500.00"))
        self.assertEqual(unit_bill.rent_amount_paid, Decimal("5000.00"))
        self.assertEqual(unit_bill.water_amount_paid, Decimal("500.00"))
        self.assertEqual(unit_bill.status, PaymentStatuses.PARTIALLY_PAID.value)
        self.assertFalse(unit_bill.fully_paid)
        self.assertEqual(rent_bill.amount_paid, Decimal("5000.00"))
        self.assertEqual(water_bill.amount_paid, Decimal("500.0000"))
        self.assertEqual(RentPayment.objects.count(), 1)
        self.assertEqual(WaterBillPayment.objects.count(), 1)
        self.assertEqual(tenant_payment.payment_type, "General Payment")
        self.assertEqual(tenant_payment.amount_paid, Decimal("5000.00"))

    def test_processing_full_payment_marks_unit_bill_paid(self):
        unit_bill = self.create_monthly_bill()

        ProcessTenantPayment(
            unit_bill=unit_bill,
            rent_amount=10000,
            water_amount=1250,
            payment_method="M-Pesa",
            payment_date=date(2026, 5, 12),
            reference_number="RCPT-002",
        ).run()

        unit_bill.refresh_from_db()

        self.assertEqual(unit_bill.status, PaymentStatuses.PAID.value)
        self.assertTrue(unit_bill.fully_paid)
        self.assertEqual(unit_bill.amount_paid, Decimal("11250.00"))

    def test_processing_rent_only_payment_records_rent_payment_type(self):
        unit_bill = self.create_monthly_bill()

        ProcessTenantPayment(
            unit_bill=unit_bill,
            rent_amount=1000,
            water_amount=0,
            payment_method="Cash",
            payment_date=date(2026, 5, 12),
            reference_number="RCPT-003",
        ).run()

        self.assertEqual(TenantPayment.objects.get().payment_type, "Rent Bill")
        self.assertEqual(WaterBillPayment.objects.count(), 0)

    def test_processing_water_only_payment_records_water_payment_type(self):
        unit_bill = self.create_monthly_bill()

        ProcessTenantPayment(
            unit_bill=unit_bill,
            rent_amount=0,
            water_amount=250,
            payment_method="Cash",
            payment_date=date(2026, 5, 12),
            reference_number="RCPT-004",
        ).run()

        self.assertEqual(TenantPayment.objects.get().payment_type, "Water Bill")
        self.assertEqual(RentPayment.objects.count(), 0)
        self.assertEqual(WaterBillPayment.objects.count(), 1)

    def test_processing_zero_payment_leaves_unit_bill_pending_without_ledgers(self):
        unit_bill = self.create_monthly_bill()

        ProcessTenantPayment(
            unit_bill=unit_bill,
            rent_amount=0,
            water_amount=0,
            payment_method="Cash",
            payment_date=date(2026, 5, 12),
            reference_number="RCPT-005",
        ).run()

        unit_bill.refresh_from_db()
        self.assertEqual(unit_bill.status, PaymentStatuses.PENDING.value)
        self.assertEqual(unit_bill.amount_paid, Decimal("0.00"))
        self.assertEqual(TenantPayment.objects.count(), 0)


class PaymentViewTests(TestCase):
    def test_payment_mutation_routes_require_login(self):
        protected_routes = [
            reverse("pay-water-bill"),
            reverse("new-expense"),
            reverse("pay-rent-bill"),
            reverse("pay-security-deposit"),
        ]

        for route in protected_routes:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 302)
                self.assertIn("/users/login/", response["Location"])
