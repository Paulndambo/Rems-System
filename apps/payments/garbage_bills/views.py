from datetime import datetime
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from apps.payments.models import (
    WaterBillPayment,
    Expense,
    RentPayment,
    RentBill,
    TenantPayment,
)
from apps.properties.models import WaterBill, PropertyUnit, Property
from apps.core.models import Month, Year

from apps.core.constants import (
    MaintenanceStatuses,
    UserRoles,
    MONTHS_LIST,
    EXPENSE_TYPES_LIST,
    PaymentMethods,
    PaymentStatuses,
    PAYMENT_METHODS,
)

from django.views.generic import ListView
from django.http import HttpRequest, JsonResponse
from django.db.models import Q
from django.db import transaction
from apps.properties.models import PropertyUnit, Property
from apps.core.models import Month, Year
from apps.payments.models import GarbageBill, GarbageBillPayment
from apps.core.due_date_normalizer import get_due_date


date_today = datetime.now().date()
# Create your views here.
class GarbageBillsView(ListView):
    model = GarbageBill
    template_name = "garbage_bills/garbage_bills.html"
    context_object_name = "garbage_bills"
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query)
                | Q(unit__name__icontains=search_query)
                | Q(unit__property__name__icontains=search_query)
                | Q(tenant__user__first_name__icontains=search_query)
                | Q(tenant__user__last_name__icontains=search_query)
            )
        return queryset.filter(fully_paid=False).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["units"] = PropertyUnit.objects.all()
        context["months"] = MONTHS_LIST
        context["years"] = Year.objects.all()
        context["properties"] = Property.objects.all()
        return context


@login_required
@transaction.atomic
def generate_garbage_bills(request: HttpRequest):
    if request.method == "POST":
        month_name = request.POST.get("month")
        year = Year.objects.get(name=str(date_today.year))

        units = PropertyUnit.objects.filter(is_occupied=True)

        month = Month.objects.get(name=month_name, year=year)

        due_date = get_due_date(month.name.capitalize(), int(year.name))

        for unit in units:
            current_month_bill = GarbageBill.objects.filter(
                unit=unit, month=month, year=year
            ).first()

            if not current_month_bill:
                GarbageBill.objects.create(
                    unit=unit,
                    tenant=unit.tenant,
                    amount_expected=unit.property.garbage_charge,
                    month=month,
                    year=year,
                    due_date=due_date,
                )
                print(f"Garbage bill generated for {unit.name} for {month_name} {year.name}")
            else:
                print(f"Garbage bill already exists for {unit.name} for {month_name} {year.name}")

        return redirect("garbage-bills")
    return render(request, "garbage_bills/new_garbage_bill.html")

# Garbage Bill Payments


class GarbageBillPaymentsView(ListView):
    model = GarbageBillPayment
    template_name = "garbage_bills/garbage_bill_payments.html"
    context_object_name = "garbage_bill_payments"
    paginate_by = 9

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query)
                | Q(garbage_bill__unit__name__icontains=search_query)
                | Q(garbage_bill__unit__property__name__icontains=search_query)
                | Q(garbage_bill__tenant__user__first_name__icontains=search_query)
                | Q(garbage_bill__tenant__user__last_name__icontains=search_query)
            )
        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["payment_methods"] = PAYMENT_METHODS
        return context


@login_required
@transaction.atomic
def pay_garbage_bill(request: HttpRequest):
    if request.method == "POST":
        garbage_bill_id = request.POST.get("garbage_bill_id")
        reference = request.POST.get("reference")
        amount_paid = request.POST.get("garbage_amount")
        payment_method = request.POST.get("payment_method")
        payment_date = request.POST.get("payment_date")

        garbage_bill = GarbageBill.objects.get(id=garbage_bill_id)
        GarbageBillPayment.objects.create(
            garbage_bill=garbage_bill,
            amount_paid=amount_paid,
            payment_method=payment_method,
            payment_date=payment_date,
        )

        garbage_bill.amount_paid += Decimal(amount_paid)
        garbage_bill.save()

        if garbage_bill.amount_paid >= garbage_bill.amount_expected:
            garbage_bill.fully_paid = True
            garbage_bill.status = PaymentStatuses.PAID.value
            garbage_bill.save()
        elif garbage_bill.amount_paid > 0:
            garbage_bill.status = PaymentStatuses.PARTIALLY_PAID.value
            garbage_bill.save()
        else:
            garbage_bill.status = PaymentStatuses.PENDING.value
            garbage_bill.save()

        TenantPayment.objects.create(
            unit=garbage_bill.unit,
            tenant=garbage_bill.tenant,
            amount_paid=amount_paid,
            payment_method=payment_method,
            payment_date=payment_date,
            payment_type="Garbage Bill",
            reference=reference,
        )

        return redirect("garbage-bills")
    return render(request, "garbage_bills/collect_garbage_payment.html")
