import requests
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
import requests
from typing import Dict, Any
from apps.payments.models import UnitMonthBill, RentBill, GarbageBill
from apps.properties.models import WaterBill
from apps.core.constants import PaymentStatuses


def format_bill_message(tenant_name: str, bill: UnitMonthBill) -> str:
    """Format WhatsApp message for unit bill notification."""
    water_bill = WaterBill.objects.filter(unit_bill=bill).first()

    total_unit_bills = sum(list(UnitMonthBill.objects.filter(tenant=bill.tenant).exclude(id=bill.id).values_list("amount_expected", flat=True)))
    total_unit_bills_paid = sum(list(UnitMonthBill.objects.filter(tenant=bill.tenant, fully_paid=True).exclude(id=bill.id).values_list("amount_paid", flat=True)))

    total_unit_bills_pending = total_unit_bills - total_unit_bills_paid

    previous_reading = 0
    current_reading = 0
    total_water_bill = 0

    if water_bill:
        previous_reading = water_bill.previous_reading
        current_reading = water_bill.current_reading
        total_water_bill = water_bill.amount

    return f"""Hello *{tenant_name}*,


This is your bill for *{bill.month.name} {bill.year.name}*.

Rent Amount: *{bill.rent_amount}*

Garbage Amount: *{bill.garbage_amount}*

*{'Water Bill Breakdown'}*
Previous Reading: *{previous_reading}* Units
Current Reading: *{current_reading}* Units
Total Water Bill: *{total_water_bill}*


*{'Pending Bills'}*: *{total_unit_bills_pending}*
*{f'Total {bill.month.name} {bill.year.name} Amount'}*: *{bill.amount_expected}*

*{'Total Amount'}*: *{Decimal(bill.amount_expected) + Decimal(total_unit_bills_pending)}*

*{'Receipt Link'}*: {bill.unit_bill_receipt_link()}

Please make the payment before the due date.

Thank you."""

class WhatsAppNotification:
    def __init__(self, message: str, recipient: str = "254745491093"):
        self.message = message
        self.phone_number = recipient
        self.instance_key = settings.WAAPI_TESTING_INSTANCE_KEY# WAAPI_INSTANCE_KEY
        self.api_key = settings.WAAPI_TESTING_API_KEY #WAAPI_API_KEY

    def send_message(self):
        """Send WhatsApp message using WaAPI."""
        url = f'https://waapi.app/api/v1/instances/{self.instance_key}/client/action/send-message'

        
        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "authorization": f"Bearer {self.api_key}"
        }
        
        payload = {
            "chatId": f"{self.phone_number}@c.us",
            "message": self.message
        }
        
        response = requests.post(url, json=payload, headers=headers)
        return response.json() if response.content else {}
