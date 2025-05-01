from datetime import datetime, date
from decimal import Decimal
from django.db.models import Sum, F, Value, Q
from django.db.models.functions import Coalesce
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.views.generic import ListView
from django.http import JsonResponse

from decimal import Decimal
from collections import defaultdict

import json
from django.contrib.auth.mixins import LoginRequiredMixin

from apps.payments.models import (WaterBillPayment, RentPayment, 
                                   RentBill, TenantPayment, GarbageBill, 
                                   GarbageBillPayment, UnitMonthBill)
from apps.properties.models import WaterBill, PropertyUnit, Property
from apps.core.models import Month, Year
from apps.core.constants import PaymentStatuses, PAYMENT_METHODS
from apps.notifications.whatsapp import WhatsAppNotification
from apps.notifications.message_templates import format_water_bill_message, format_rent_bill_message, format_garbage_bill_message, format_unit_bill_message
from apps.core.constants import MONTHS_LIST, PAYMENT_METHODS
from apps.properties.water_bills.billing_mixin import TenantBillingMixin


class MonthlyUnitBillsView(LoginRequiredMixin, ListView):
    model = Month
    template_name = "unit_bills/monthly_unit_bills.html"
    context_object_name = "months"

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")
        month_ids = list(UnitMonthBill.objects.values_list("month_id", flat=True))

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query) | Q(name__icontains=search_query)
            )
        return queryset.filter(id__in=month_ids).order_by("-created_at")


class UnitMonthBillsView(LoginRequiredMixin, ListView):
    model = UnitMonthBill
    template_name = "unit_bills/unit_bills.html"
    context_object_name = "unit_bills"

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")
        month = self.kwargs.get("month_id")

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query) |
                Q(unit__name__icontains=search_query) |
                Q(unit__property__name__icontains=search_query) |
                Q(tenant__user__first_name__icontains=search_query) |
                Q(tenant__user__last_name__icontains=search_query)
            )
        return queryset.filter(month_id=month).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["payment_methods"] = PAYMENT_METHODS
        return context


@login_required
def unit_bill_details(request, pk):
    unit_bill = UnitMonthBill.objects.get(id=pk)
    payments = TenantPayment.objects.filter(unit_bill=unit_bill)

    context = {
        "unit_bill": unit_bill,
        "payments": payments,
        "payment_methods": PAYMENT_METHODS
    }
    return render(request, "unit_bills/unit_bill_details.html", context)


@login_required
def unit_bill_receipt(request, unit_bill_id):
    bill = UnitMonthBill.objects.get(id=unit_bill_id)
    context = {
        "bill": bill
    }
    return render(request, "unit_bills/unit_bill_receipt.html", context)


def update_bill_status(bill, amount_paid, expected_amount):
    if amount_paid >= expected_amount:
        bill.fully_paid = True
        bill.status = PaymentStatuses.PAID.value
        
        whatsapp_notification = WhatsAppNotification(
            message=format_unit_bill_message(bill.tenant.user.first_name, bill.month.name, bill.year.name),
            recipient=bill.tenant.user.phone_number
        )
        whatsapp_notification.send_message()
        
    elif amount_paid > 0:
        bill.status = PaymentStatuses.PARTIALLY_PAID.value
    else:
        bill.status = PaymentStatuses.PENDING.value
    bill.save()


@login_required
@transaction.atomic
def collect_unit_bill_payment(request):
    if request.method == "POST":
        unit_bill_id = request.POST.get("unit_bill_id")
        rent_amount = Decimal(request.POST.get("rent_amount", 0))
        water_amount = Decimal(request.POST.get("water_amount", 0))
        garbage_amount = Decimal(request.POST.get("garbage_amount", 0))
        payment_method = request.POST.get("payment_method")
        payment_date = request.POST.get("payment_date")

        unit_bill = UnitMonthBill.objects.get(id=unit_bill_id)

        if rent_amount > 0:
            rent_bill = RentBill.objects.get(unit_bill=unit_bill)
            rent_bill.amount_paid += rent_amount
            rent_bill.save()
            unit_bill.rent_amount_paid += rent_amount
            unit_bill.amount_paid += rent_amount
            unit_bill.save()
            update_bill_status(rent_bill, rent_bill.amount_paid, rent_bill.amount_expected)

            rent_payment = RentPayment.objects.create(
                rent_bill=rent_bill,
                amount_paid=rent_amount,
                payment_method=payment_method,
                payment_date=payment_date
            )

            TenantPayment.objects.create(
                unit_bill=unit_bill,
                tenant=unit_bill.tenant,
                unit=unit_bill.unit,
                rent_payment=rent_payment,
                amount_paid=rent_amount,
                payment_method=payment_method,
                payment_date=payment_date,
                payment_type="Rent Bill",
                month=unit_bill.month,
                year=unit_bill.year
            )

            
            whatsapp_notification = WhatsAppNotification(
                message=format_rent_bill_message(unit_bill.tenant.user.first_name, rent_amount),
                recipient=unit_bill.tenant.user.phone_number
            )
            whatsapp_notification.send_message()
            

        if water_amount > 0:
            water_bill = WaterBill.objects.get(unit_bill=unit_bill)
            water_bill.amount_paid += water_amount
            water_bill.save()
            unit_bill.water_amount_paid += water_amount
            unit_bill.amount_paid += water_amount
            unit_bill.save()
            update_bill_status(water_bill, water_bill.amount_paid, water_bill.amount)

            water_payment = WaterBillPayment.objects.create(
                tenant=unit_bill.tenant,
                water_bill=water_bill,
                amount_paid=water_amount,
                payment_method=payment_method,
                payment_date=payment_date,
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
                payment_date=payment_date,
                payment_type="Water Bill",
                month=unit_bill.month,
                year=unit_bill.year
            )
            
            whatsapp_notification = WhatsAppNotification(
                message=format_water_bill_message(unit_bill.tenant.user.first_name, water_amount),
                recipient=unit_bill.tenant.user.phone_number
            )
            whatsapp_notification.send_message()
            

        if garbage_amount > 0:
            garbage_bill = GarbageBill.objects.get(unit_bill=unit_bill)
            garbage_bill.amount_paid += garbage_amount
            garbage_bill.save()
            unit_bill.garbage_amount_paid += garbage_amount
            unit_bill.amount_paid += garbage_amount
            unit_bill.save()
            update_bill_status(garbage_bill, garbage_bill.amount_paid, unit_bill.garbage_amount)

            garbage_payment = GarbageBillPayment.objects.create(
                garbage_bill=garbage_bill,
                amount_paid=garbage_amount,
                payment_method=payment_method,
                payment_date=payment_date
            )

            TenantPayment.objects.create(
                unit_bill=unit_bill,
                tenant=unit_bill.tenant,
                unit=unit_bill.unit,
                garbage_bill_payment=garbage_payment,
                amount_paid=garbage_amount,
                payment_method=payment_method,
                payment_date=payment_date,
                payment_type="Garbage Bill",
                month=unit_bill.month,
                year=unit_bill.year
            )

            
            whatsapp_notification = WhatsAppNotification(
                message=format_garbage_bill_message(unit_bill.tenant.user.first_name, garbage_amount),
                recipient=unit_bill.tenant.user.phone_number
            )
            whatsapp_notification.send_message()
            

        update_bill_status(unit_bill, unit_bill.amount_paid, unit_bill.amount_expected)

        return redirect("unit-bill-details", pk=unit_bill_id)
    return render(request, "unit_bills/collect_payment.html")


class PendingBillsView(LoginRequiredMixin, ListView):
    model = UnitMonthBill
    template_name = "unit_bills/pending_bills.html"
    context_object_name = "pending_bills"

    def get_queryset(self):
        # Not used in this version
        return UnitMonthBill.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        search_query = self.request.GET.get("search", "")

        queryset = UnitMonthBill.objects.filter(fully_paid=False)

        if search_query:
            queryset = queryset.filter(
                Q(unit__name__icontains=search_query) |
                Q(unit__property__name__icontains=search_query) |
                Q(tenant__user__first_name__icontains=search_query) |
                Q(tenant__user__last_name__icontains=search_query)
            )

        # Group unpaid bills by unit
        grouped_bills = {}

        for bill in queryset.select_related("unit", "tenant", "tenant__user"):
            unit_name = bill.unit.name if bill.unit else "Unknown Unit"
            unit_id = bill.unit.id if bill.unit else None

            key = unit_id  # safer to use ID as key
            if key not in grouped_bills:
                grouped_bills[key] = {
                    "unit_name": unit_name,
                    "tenant": f"{bill.tenant.user.first_name} {bill.tenant.user.last_name}" if bill.tenant and bill.tenant.user else "Unknown Tenant",
                    "total_unpaid": Decimal("0.00"),
                    "bills": []
                }

            balance = Decimal(bill.amount_expected) - Decimal(bill.amount_paid)
            grouped_bills[key]["total_unpaid"] += balance
            grouped_bills[key]["bills"].append(bill)

        context["pending_bills"] = grouped_bills.values()
        return context
    
    
def generate_bill(request):
    units = PropertyUnit.objects.filter(is_occupied=True)
    properties = Property.objects.all()
    
    context = {
        "months": MONTHS_LIST,
        "years": Year.objects.filter(is_active=True),
        "payment_methods": PAYMENT_METHODS,
        "units": units,
        "properties": properties
    }
    
    if request.method == "POST":
        unit_id = request.POST.get('unit')
        unit = PropertyUnit.objects.get(name=unit_id)

        print("**************Unit Data**************")
        print(f"Unit: {unit_id}")
        print("**************Unit Data**************")
        
        last_water_bill = WaterBill.objects.filter(unit=unit).order_by("-created_at").first()
        
        year_id = request.POST.get('year')
        month_name = request.POST.get('month')
        previous_reading = last_water_bill.current_reading if last_water_bill else 0
        current_reading = request.POST.get('current_reading')
        
        
        year = Year.objects.get(id=year_id)
        month = Month.objects.get(name=month_name, year=year)
        
        try:
            biller = TenantBillingMixin(
                year=year,
                month=month,
                previous_reading=previous_reading,
                current_reading=current_reading,
                unit=unit
            )
            res = biller.generate_bill()
            messages.success(request, f"Bill successfully generated!!, You can go to monthly bills for {month}, {year.name}. You will find it")
            return redirect(f"/payments/unit-bills/{month.id}/")
        except Exception as e:
            raise e
        
        
    
    return render(request, "water_bills/generate_bill.html", context)
