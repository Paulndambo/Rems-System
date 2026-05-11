import csv
from datetime import date
from decimal import Decimal
from io import StringIO

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.core.models import Month, Year
from apps.payments.models import TenantPayment
from apps.properties.models import Property, PropertyUnit
from apps.reports.utils import generate_csv
from apps.tenants.models import Tenant


class ReportUtilsTests(TestCase):
    def test_generate_csv_writes_header_and_payment_rows(self):
        owner = get_user_model().objects.create(username="owner")
        tenant_user = get_user_model().objects.create(
            username="tenant",
            first_name="Test",
            last_name="Tenant",
        )
        tenant = Tenant.objects.create(user=tenant_user)
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
            rent=Decimal("10000.00"),
            tenant=tenant,
        )
        year = Year.objects.create(name="2026")
        month = Month.objects.create(name="May", year=year)
        payment = TenantPayment.objects.create(
            tenant=tenant,
            unit=unit,
            amount_paid=Decimal("5000.00"),
            payment_method="Cash",
            payment_date=date(2026, 5, 12),
            payment_type="Rent",
            month=month,
            year=year,
        )
        response = StringIO()

        generate_csv(response, [payment])

        response.seek(0)
        rows = list(csv.reader(response))
        self.assertEqual(
            rows[0],
            [
                "#",
                "Tenant",
                "House No.",
                "Amount Paid",
                "Payment Method",
                "Payment Date",
                "Month",
                "Year",
                "Payment Type",
            ],
        )
        self.assertEqual(
            rows[1],
            [
                "1",
                "Test Tenant",
                "A1",
                "5000.00",
                "Cash",
                "2026-05-12",
                "May",
                f"2026-({year.id})",
                "Rent",
            ],
        )
