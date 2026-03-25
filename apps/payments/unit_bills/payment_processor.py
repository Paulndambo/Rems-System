from datetime import datetime, date

from django.db import transaction


from decimal import Decimal
from collections import defaultdict

import json


from apps.payments.models import (
    WaterBillPayment,
    RentPayment,
    RentBill,
    TenantPayment,
    GarbageBill,
    GarbageBillPayment,
    UnitMonthBill,
)
from apps.properties.models import WaterBill, PropertyUnit, Property
from apps.core.models import Month, Year
from apps.core.constants import PaymentStatuses, PAYMENT_METHODS
from apps.notifications.whatsapp import WhatsAppNotification
from apps.notifications.message_templates import format_bill_payment_message
from apps.core.constants import MONTHS_LIST, PAYMENT_METHODS


class ProcessTenantPayment(object):
    def __init__(
        self,
        unit_bill: UnitMonthBill,
        rent_amount: float,
        water_amount: float,
        garbage_amount: float,
        payment_method: str,
        payment_date: date,

    ) -> None:
        self.unit_bill = unit_bill
        self.rent_amount = rent_amount
        self.water_amount = water_amount
        self.garbage_amount = garbage_amount
        self.payment_method = payment_method
        self.payment_date = payment_date

    @transaction.atomic
    def run(self):
        try:
            if self.rent_amount > 0:
                self.__record_rent_payment()

            if self.water_amount > 0:
                self.__record_water_payment()

            if self.garbage_amount > 0:
                self.__record_garbage_payment()

            self.__send_payment_notification()
        except Exception as e:
            raise e

    def __record_rent_payment(self):
        rent_bill = RentBill.objects.get(unit_bill=self.unit_bill)
        rent_bill.amount_paid += self.rent_amount
        rent_bill.save()
        self.unit_bill.rent_amount_paid += self.rent_amount
        self.unit_bill.amount_paid += self.rent_amount
        self.unit_bill.save()

        rent_payment = RentPayment.objects.create(
            rent_bill=rent_bill,
            amount_paid=self.rent_amount,
            payment_method=self.payment_method,
            payment_date=self.payment_date,
        )

        TenantPayment.objects.create(
            unit_bill=self.unit_bill,
            tenant=self.unit_bill.tenant,
            unit=self.unit_bill.unit,
            rent_payment=rent_payment,
            amount_paid=self.rent_amount,
            payment_method=self.payment_method,
            payment_date=self.payment_date,
            payment_type="Rent Bill",
            month=self.unit_bill.month,
            year=self.unit_bill.year,
        )

    def __record_water_payment(self):
        water_bill = WaterBill.objects.get(unit_bill=self.unit_bill)
        water_bill.amount_paid += self.water_amount
        water_bill.save()
        self.unit_bill.water_amount_paid += self.water_amount
        self.unit_bill.amount_paid += self.water_amount
        self.unit_bill.save()

        water_payment = WaterBillPayment.objects.create(
            tenant=self.unit_bill.tenant,
            water_bill=water_bill,
            amount_paid=self.water_amount,
            payment_method=self.payment_method,
            payment_date=self.payment_date,
            month=self.unit_bill.month,
            year=self.unit_bill.year,
        )

        TenantPayment.objects.create(
            unit_bill=self.unit_bill,
            tenant=self.unit_bill.tenant,
            unit=self.unit_bill.unit,
            water_bill_payment=water_payment,
            amount_paid=self.water_amount,
            payment_method=self.payment_method,
            payment_date=self.payment_date,
            payment_type="Water Bill",
            month=self.unit_bill.month,
            year=self.unit_bill.year,
        )

    def __record_garbage_payment(self):
        garbage_bill = GarbageBill.objects.get(unit_bill=self.unit_bill)
        garbage_bill.amount_paid += self.garbage_amount
        garbage_bill.save()
        self.unit_bill.garbage_amount_paid += self.garbage_amount
        self.unit_bill.amount_paid += self.garbage_amount
        self.unit_bill.save()

        garbage_payment = GarbageBillPayment.objects.create(
            garbage_bill=garbage_bill,
            amount_paid=self.garbage_amount,
            payment_method=self.payment_method,
            payment_date=self.payment_date,
        )

        TenantPayment.objects.create(
            unit_bill=self.unit_bill,
            tenant=self.unit_bill.tenant,
            unit=self.unit_bill.unit,
            garbage_bill_payment=garbage_payment,
            amount_paid=self.garbage_amount,
            payment_method=self.payment_method,
            payment_date=self.payment_date,
            payment_type="Garbage Bill",
            month=self.unit_bill.month,
            year=self.unit_bill.year,
        )

    def __create_tenant_payment(self, unit_bill, *args):
        pass

    def __send_payment_notification(self):
        try:
            amount_paid = (
                Decimal(self.rent_amount)
                + Decimal(self.garbage_amount)
                + Decimal(self.water_amount)
            )
            if self.unit_bill.amount_paid >= self.unit_bill.amount_expected:
                self.unit_bill.fully_paid = True
                self.unit_bill.status = PaymentStatuses.PAID.value
                self.unit_bill.save()
            elif self.unit_bill.amount_paid > 0 and self.unit_bill.amount_paid < self.unit_bill.amount_expected:
                self.unit_bill.status = PaymentStatuses.PARTIALLY_PAID.value
                self.unit_bill.save()
            else:
                self.unit_bill.status = PaymentStatuses.PENDING.value
                self.unit_bill.save()

            whatsapp_notification = WhatsAppNotification(
                message=format_bill_payment_message(
                    tenant_name=f"{self.unit_bill.tenant.user.first_name} {self.unit_bill.tenant.user.last_name}",
                    rent_amount=self.rent_amount,
                    garbage_amount=self.garbage_amount,
                    water_amount=self.water_amount,
                ),
                recipient=self.unit_bill.tenant.user.phone,
            )
            whatsapp_notification.send_message()
            success = True
        except Exception as e:
            raise e