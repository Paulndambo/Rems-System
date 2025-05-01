from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.conf import settings
import requests
from typing import Dict, Any
from apps.payments.models import UnitMonthBill, RentBill, GarbageBill
from apps.properties.models import WaterBill
from apps.core.constants import PaymentStatuses
from apps.notifications.sms_sender import TiaraConnectSMSManager


def send_unit_bill_notification(request):
    """View to send WhatsApp notification for unit bill."""
    if request.method == 'POST':
        unit_bill_id = request.POST.get('unit_bill_id')
        notification_type = request.POST.get("notification_type")
        unit_bill = get_object_or_404(UnitMonthBill, id=unit_bill_id)
        tenant = unit_bill.tenant

        if notification_type == "sms":
            print(f"Notification Type is: {notification_type}")

            notifier = TiaraConnectSMSManager(
                phone_number=tenant.user.phone,
                message_type="rent_reminder"
            )
            notifier.send_rent_reminder(bill=unit_bill)

        else:
            return redirect('unit-bills', unit_bill.month.id)
        return redirect('unit-bills', unit_bill.month.id)
   
    return render(request, 'notifications/send_unit_bill_notification.html')
