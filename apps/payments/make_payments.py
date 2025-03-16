from apps.payments.models import RentBill, UnitMonthBill, RentPayment, WaterBillPayment, TenantPayment, RentPayment, GarbageBillPayment, GarbageBill
from apps.core.models import Month, Year
from apps.core.constants import PaymentMethods, MaintenanceStatuses

from apps.properties.models import WaterBill
from datetime import datetime
from django.db import transaction



@transaction.atomic
def mark_water_payments():
    water_bills = WaterBill.objects.filter(month__year__name="2025", month__name__in=["January", "February"])

    for water_bill in water_bills:
        water_bill_payment = WaterBillPayment.objects.create(
            tenant=water_bill.unit.tenant,
            water_bill=water_bill,
            amount_paid=water_bill.amount,
            payment_method=PaymentMethods.MPESA.value,
            payment_date=water_bill.due_date,
            month=water_bill.month,
            year=water_bill.year,
        )

        TenantPayment.objects.create(
            unit_bill=water_bill.unit_bill,
            unit=water_bill.unit,
            tenant=water_bill.unit.tenant,
            water_bill_payment=water_bill_payment,
            amount_paid=water_bill.amount,
            payment_method=PaymentMethods.MPESA.value,
            payment_date=water_bill.due_date,
            month=water_bill.month,
            year=water_bill.year,
            payment_type="Water Bill",
        )

        water_bill.fully_paid = True
        water_bill.status = MaintenanceStatuses.PAID.value
        water_bill.amount_paid = water_bill.amount
        water_bill.save()


@transaction.atomic
def mark_garbage_payments():
    garbage_bills = GarbageBill.objects.filter(unit_bill__month__year__name="2025", unit_bill__month__name__in=["January", "February"])

    for garbage_bill in garbage_bills:
        garbage_bill_payment = GarbageBillPayment.objects.create(
            garbage_bill=garbage_bill,
            amount_paid=garbage_bill.amount_expected,
            payment_method=PaymentMethods.MPESA.value,
            payment_date=garbage_bill.due_date,
        )

        TenantPayment.objects.create(
            unit_bill=garbage_bill.unit_bill,
            unit=garbage_bill.unit,
            tenant=garbage_bill.unit.tenant,
            garbage_bill_payment=garbage_bill_payment,
            amount_paid=garbage_bill.amount_expected,
            payment_method=PaymentMethods.MPESA.value,
            payment_date=garbage_bill.due_date,
            month=garbage_bill.unit_bill.month,
            year=garbage_bill.unit_bill.year,
            payment_type="Garbage Bill",
        )

        garbage_bill.fully_paid = True
        garbage_bill.status = MaintenanceStatuses.PAID.value
        garbage_bill.amount_paid = garbage_bill.amount_expected
        garbage_bill.save()


@transaction.atomic
def mark_rent_payments():
    rent_bills = RentBill.objects.filter(unit_bill__month__year__name="2025", unit_bill__month__name__in=["January", "February"])

    for rent_bill in rent_bills:
        rent_bill_payment = RentPayment.objects.create(
            rent_bill=rent_bill,
            amount_paid=rent_bill.amount_expected,
            payment_method=PaymentMethods.MPESA.value,
            payment_date=rent_bill.due_date
        )

        TenantPayment.objects.create(
            unit_bill=rent_bill.unit_bill,
            unit=rent_bill.unit,
            tenant=rent_bill.tenant,
            rent_payment=rent_bill_payment,
            amount_paid=rent_bill.amount_expected,
            payment_method=PaymentMethods.MPESA.value,
            payment_date=rent_bill.due_date,
            month=rent_bill.month,
            year=rent_bill.year,
            payment_type="Rent Bill",
        )

        rent_bill.fully_paid = True
        rent_bill.status = MaintenanceStatuses.PAID.value
        rent_bill.amount_paid = rent_bill.amount_expected
        rent_bill.save()


@transaction.atomic
def mark_unit_bill_payments():
    unit_bills = UnitMonthBill.objects.filter(month__year__name="2025", month__name__in=["January", "February"])

    for unit_bill in unit_bills:
        unit_bill.mark_as_paid()
