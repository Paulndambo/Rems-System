from datetime import datetime
from apps.payments.models import UnitMonthBill
from apps.core.constants import PaymentStatuses, PaymentMethods
from decimal import Decimal
from apps.payments.models import (
    RentBill,
    GarbageBill,
    RentPayment,
    WaterBillPayment,
    GarbageBillPayment,
    TenantPayment,
)
from apps.properties.models import WaterBill
from django.db import transaction


def update_bill_status(bill, amount_paid, expected_amount):
    if amount_paid >= expected_amount:
        bill.fully_paid = True
        bill.status = PaymentStatuses.PAID.value
    elif amount_paid > 0:
        bill.status = PaymentStatuses.PARTIALLY_PAID.value
    else:
        bill.status = PaymentStatuses.PENDING.value
    bill.save()


class BulkPaymentsProcessor:
    def __init__(self):
        pass

    def process_payments(self, unit_bill):
        unit_bill_id = unit_bill.id
        rent_amount = unit_bill.rent_amount
        water_amount = unit_bill.water_amount
        garbage_amount = unit_bill.garbage_amount
        payment_method = PaymentMethods.MPESA.value

        unit_bill = UnitMonthBill.objects.get(id=unit_bill_id)

        if rent_amount > 0:
            rent_bill = RentBill.objects.filter(unit_bill=unit_bill).first()
            rent_bill.amount_paid += rent_amount
            rent_bill.save()
            unit_bill.rent_amount_paid += rent_amount
            unit_bill.amount_paid += rent_amount
            unit_bill.save()
            update_bill_status(
                rent_bill, rent_bill.amount_paid, rent_bill.amount_expected
            )

            rent_payment = RentPayment.objects.create(
                rent_bill=rent_bill,
                amount_paid=rent_amount,
                payment_method=payment_method,
                payment_date=rent_bill.due_date,
            )

            TenantPayment.objects.create(
                unit_bill=unit_bill,
                tenant=unit_bill.tenant,
                unit=unit_bill.unit,
                rent_payment=rent_payment,
                amount_paid=rent_amount,
                payment_method=payment_method,
                payment_date=rent_bill.due_date,
                payment_type="Rent Bill",
                month=unit_bill.month,
                year=unit_bill.year,
            )

        if water_amount > 0:
            water_bill = WaterBill.objects.filter(unit_bill=unit_bill).first()
            if water_bill:
                water_bill.amount_paid += water_amount
                water_bill.save()
                unit_bill.water_amount_paid += water_amount
                unit_bill.amount_paid += water_amount
                unit_bill.save()
                update_bill_status(
                    water_bill, water_bill.amount_paid, water_bill.amount
                )

                water_payment = WaterBillPayment.objects.create(
                    tenant=unit_bill.tenant,
                    water_bill=water_bill,
                    amount_paid=water_amount,
                    payment_method=payment_method,
                    payment_date=water_bill.due_date,
                    month=unit_bill.month,
                    year=unit_bill.year,
                )

                TenantPayment.objects.create(
                    unit_bill=unit_bill,
                    tenant=unit_bill.tenant,
                    unit=unit_bill.unit,
                    water_bill_payment=water_payment,
                    amount_paid=water_amount,
                    payment_method=payment_method,
                    payment_date=water_bill.due_date,
                    payment_type="Water Bill",
                    month=unit_bill.month,
                    year=unit_bill.year,
                )

        if garbage_amount > 0:
            garbage_bill = GarbageBill.objects.filter(unit_bill=unit_bill).first()
            garbage_bill.amount_paid += garbage_amount
            garbage_bill.save()
            unit_bill.garbage_amount_paid += garbage_amount
            unit_bill.amount_paid += garbage_amount
            unit_bill.save()
            update_bill_status(
                garbage_bill, garbage_bill.amount_paid, unit_bill.garbage_amount
            )

            garbage_payment = GarbageBillPayment.objects.create(
                garbage_bill=garbage_bill,
                amount_paid=garbage_amount,
                payment_method=payment_method,
                payment_date=garbage_bill.due_date,
            )

            TenantPayment.objects.create(
                unit_bill=unit_bill,
                tenant=unit_bill.tenant,
                unit=unit_bill.unit,
                garbage_bill_payment=garbage_payment,
                amount_paid=garbage_amount,
                payment_method=payment_method,
                payment_date=garbage_bill.due_date,
                payment_type="Garbage Bill",
                month=unit_bill.month,
                year=unit_bill.year,
            )

        update_bill_status(unit_bill, unit_bill.amount_paid, unit_bill.amount_expected)
