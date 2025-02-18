from datetime import datetime, date
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from django.views.generic import ListView
from django.http import JsonResponse
from django.db.models import Q
import json

from apps.payments.models import (WaterBillPayment, Expense, RentPayment, 
                                   RentBill, TenantPayment, GarbageBill, 
                                   GarbageBillPayment, UnitMonthBill)
from apps.properties.models import WaterBill, PropertyUnit, Property
from apps.core.models import Month, Year
from apps.core.constants import PaymentStatuses, PAYMENT_METHODS
from apps.notifications.whatsapp import WhatsAppNotification
from apps.notifications.message_templates import format_water_bill_message, format_rent_bill_message, format_garbage_bill_message, format_unit_bill_message

class MonthlyUnitBillsView(ListView):
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


class UnitMonthBillsView(ListView):
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


def unit_bill_details(request, pk):
    unit_bill = UnitMonthBill.objects.get(id=pk)
    payments = TenantPayment.objects.filter(unit_bill=unit_bill)

    context = {
        "unit_bill": unit_bill,
        "payments": payments,
        "payment_methods": PAYMENT_METHODS
    }
    return render(request, "unit_bills/unit_bill_details.html", context)


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


class PendingBillsView(ListView):
    model = UnitMonthBill
    template_name = "unit_bills/pending_bills.html"
    context_object_name = "pending_bills"

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")
    

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query) |
                Q(unit__name__icontains=search_query) |
                Q(unit__property__name__icontains=search_query) |
                Q(tenant__user__first_name__icontains=search_query) |
                Q(tenant__user__last_name__icontains=search_query)
            )
        return queryset.filter(fully_paid=False).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context