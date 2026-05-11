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
        payment_method: str,
        payment_date: date,
        reference_number: str = None,
    ) -> None:
        self.unit_bill = unit_bill
        self.rent_amount = rent_amount
        self.water_amount = water_amount
        self.payment_method = payment_method
        self.reference_number = reference_number
        self.payment_date = payment_date

    @transaction.atomic
    def run(self):
        try:
            if self.rent_amount > 0:
                self.__record_rent_payment()

            if self.water_amount > 0:
                self.__record_water_payment()
            self.__record_tenant_payment(unit_bill=self.unit_bill)
            self.__send_payment_notification()
        except Exception as e:
            raise e

    def __record_rent_payment(self):
        rent_bill = RentBill.objects.get(unit_bill=self.unit_bill)
        rent_bill.amount_paid += Decimal(str(self.rent_amount))
        rent_bill.save()

        self.unit_bill.rent_amount_paid += Decimal(str(self.rent_amount))
        self.unit_bill.amount_paid += Decimal(str(self.rent_amount))
        self.unit_bill.save()

        RentPayment.objects.create(
            rent_bill=rent_bill,
            amount_paid=self.rent_amount,
            payment_method=self.payment_method,
            payment_date=self.payment_date,
        )

    def __record_water_payment(self):
        water_bill = WaterBill.objects.get(unit_bill=self.unit_bill)
        water_bill.amount_paid += Decimal(str(self.water_amount))
        water_bill.save()

        self.unit_bill.water_amount_paid += Decimal(str(self.water_amount))
        self.unit_bill.amount_paid += Decimal(str(self.water_amount))
        self.unit_bill.save()

        WaterBillPayment.objects.create(
            tenant=self.unit_bill.tenant,
            water_bill=water_bill,
            amount_paid=self.water_amount,
            payment_method=self.payment_method,
            payment_date=self.payment_date,
            month=self.unit_bill.month,
            year=self.unit_bill.year,
        )
    
    def __record_tenant_payment(self, unit_bill: UnitMonthBill):
        if self.rent_amount > 0 and self.water_amount > 0:
            TenantPayment.objects.create(
                reference=self.reference_number,
                tenant=unit_bill.tenant,
                unit=unit_bill.unit,
                amount_paid=self.rent_amount,
                payment_method=self.payment_method,
                payment_date=self.payment_date,
                payment_type="General Payment",
                month=unit_bill.month,
                year=unit_bill.year,
            )

        elif self.rent_amount > 0 and self.water_amount == 0:
            TenantPayment.objects.create(
                reference=self.reference_number,
                tenant=unit_bill.tenant,
                unit=unit_bill.unit,
                amount_paid=self.rent_amount,
                payment_method=self.payment_method,
                payment_date=self.payment_date,
                payment_type="Rent Bill",
                month=unit_bill.month,
                year=unit_bill.year,
            )
        elif self.water_amount > 0 and self.rent_amount == 0:
            TenantPayment.objects.create(
                reference=self.reference_number,
                tenant=unit_bill.tenant,
                unit=unit_bill.unit,
                amount_paid=self.water_amount,
                payment_method=self.payment_method,
                payment_date=self.payment_date,
                payment_type="Water Bill",
                month=unit_bill.month,
                year=unit_bill.year,
            )
        else:
            pass


    def __send_payment_notification(self):
        try:
            
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

            #whatsapp_notification = WhatsAppNotification(
            #    message=format_bill_payment_message(
            #        tenant_name=f"{self.unit_bill.tenant.user.first_name} {self.unit_bill.tenant.user.last_name}",
            #        rent_amount=self.rent_amount,
            #        garbage_amount=self.garbage_amount,
            #        water_amount=self.water_amount,
            #    ),
            #    recipient=self.unit_bill.tenant.user.phone,
            #)
            #whatsapp_notification.send_message()
            #success = True
        except Exception as e:
            raise e