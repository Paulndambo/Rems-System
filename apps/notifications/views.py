from decimal import Decimal
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


def send_whatsapp_message(recipient: str, message: str) -> Dict[str, Any]:
    """Send WhatsApp message using WaAPI."""
    url = f'https://waapi.app/api/v1/instances/{settings.WAAPI_INSTANCE_KEY}/client/action/send-message'
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {settings.WAAPI_API_KEY}"
    }
    
    payload = {
        "chatId": f"{recipient}@c.us",
        "message": message
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json() if response.content else {}

def send_unit_bill_notification(request):
    """View to send WhatsApp notification for unit bill."""
    if request.method == 'POST':
        unit_bill_id = request.POST.get('unit_bill_id')
        unit_bill = get_object_or_404(UnitMonthBill, id=unit_bill_id)
        tenant = unit_bill.tenant
        
        # TODO: Get recipient number from tenant model instead of hardcoding
        recipient_number = tenant.user.phone
        
        tenant_name = f"{tenant.user.first_name} {tenant.user.last_name}"
        message = format_bill_message(tenant_name, unit_bill)
        
        try:
            send_whatsapp_message(recipient_number, message)
            success = True
            unit_bill.whatsapp_notification_sent = True
            unit_bill.save()
        except requests.RequestException as e:
            print(f"Failed to send WhatsApp message: {str(e)}")
            success = False

        return redirect('unit-bills', unit_bill.month.id)
   
    return render(request, 'notifications/send_unit_bill_notification.html')
