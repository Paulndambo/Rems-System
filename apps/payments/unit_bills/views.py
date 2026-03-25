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
from datetime import datetime, date
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
from apps.payments.unit_bills.payment_processor import ProcessTenantPayment


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
    
    previous_bills = UnitMonthBill.objects.filter(tenant=bill.tenant).exclude(id=bill.id)
    
    total_rent_bills = sum(previous_bills.values_list("rent_amount", flat=True))
    total_rent_bills_paid = sum(previous_bills.values_list("rent_amount_paid", flat=True))
    
    total_water_bills = sum(previous_bills.values_list("water_amount", flat=True))
    total_water_bills_paid = sum(previous_bills.values_list("water_amount_paid", flat=True))
    
    total_water_bills_pending = total_water_bills - total_water_bills_paid
    total_rent_pending = total_rent_bills - total_rent_bills_paid
    
    total_month_bill = total_rent_pending + total_water_bills_pending + bill.amount_expected
    
    context = {
        "bill": bill,
        "total_month_bill": total_month_bill,
        "total_rent_pending": total_rent_pending,
        "total_water_bills_pending": total_water_bills_pending,
        "total_pending_bill": total_rent_pending + total_water_bills_pending,
    }
    return render(request, "unit_bills/unit_bill_receipt.html", context)


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

        ProcessTenantPayment(
            unit_bill = unit_bill,
            rent_amount = rent_amount,
            water_amount = water_amount,
            garbage_amount = garbage_amount,
            payment_method = payment_method,
            payment_date = payment_date
        ).run()

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
    
@login_required    
def generate_bill(request):
    properties = Property.objects.all()

    context = {
        "months": MONTHS_LIST,
        "payment_methods": PAYMENT_METHODS,
        "properties": properties
    }

    if request.method == "POST":
        try:
            unit_id = request.POST.get('unit')
            month_name = request.POST.get('month')
            current_reading = request.POST.get('current_reading')

            if not unit_id:
                messages.error(request, "Please select a unit.")
                return redirect("generate-bill")

            unit = PropertyUnit.objects.get(id=unit_id)

            last_water_bill = WaterBill.objects.filter(unit=unit).order_by("-created_at").first()
            previous_reading = last_water_bill.current_reading if last_water_bill else 0

            year = Year.objects.get(name=str(datetime.now().year))
            month = Month.objects.get(name=month_name, year=year)

            biller = TenantBillingMixin(
                year=year,
                month=month,
                previous_reading=previous_reading,
                current_reading=current_reading,
                unit=unit
            )

            biller.generate_bill()

            messages.success(
                request,
                f"Bill successfully generated for {unit.name} - {month.name} {year.name}"
            )

            return redirect(f"/payments/unit-bills/{month.id}/")

        except Exception as e:
            messages.error(request, str(e))
            return redirect("generate-bill")

    return render(request, "water_bills/generate_bill.html", context)


@login_required
def get_units_by_property(request):
    property_id = request.GET.get("property_id")

    units = PropertyUnit.objects.filter(
        property_id=property_id,
        is_occupied=True
    ).select_related("property")

    data = [
        {
            "id": unit.id,
            "name": f"{unit.name} - {unit.property.name}"
        }
        for unit in units
    ]

    return JsonResponse(data, safe=False)
