from datetime import datetime
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.contrib import messages
from apps.payments.models import WaterBillPayment, Expense, RentPayment, RentBill, TenantPayment
from apps.properties.models import WaterBill, PropertyUnit, Property
from apps.core.models import Month, Year

from apps.core.constants import MaintenanceStatuses, UserRoles, MONTHS_LIST, EXPENSE_TYPES_LIST, PaymentMethods, PaymentStatuses, PAYMENT_METHODS

from django.views.generic import ListView
from django.http import JsonResponse
from django.db.models import Q
from django.db import transaction
from datetime import date
from calendar import month_name
import json
from apps.properties.models import PropertyUnit, Property
from apps.core.models import Month, Year
from apps.payments.models import GarbageBill, GarbageBillPayment, UnitMonthBill


# Create your views here.
class GarbageBillsView(ListView):
    model = GarbageBill
    template_name = "garbage_bills/garbage_bills.html"
    context_object_name = "garbage_bills"


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
        return queryset.order_by("-created_at")


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['units'] = PropertyUnit.objects.all()
        context['months'] = MONTHS_LIST
        context['years'] = Year.objects.all()
        context['properties'] = Property.objects.all()
        return context

@login_required
@transaction.atomic
def generate_garbage_bills(request):
    if request.method == "POST":
        print("****************This post request is coming *****************")

        property_id = request.POST.get("property")
        month = request.POST.get("month")

        year = request.POST.get("year")
        due_date = request.POST.get("date_due")

        
        year = Year.objects.get(id=year)
        month = Month.objects.get(name=month, year=year)
        

        units = PropertyUnit.objects.filter(property_id=property_id, is_occupied=True)

        for unit in units:
            unit_bill = UnitMonthBill.objects.filter(unit=unit, month=month, year=year).first() 

            if not unit_bill:
                unit_bill = UnitMonthBill.objects.create(
                    unit=unit, 
                    tenant=unit.tenant,
                    rent_amount=unit.rent,
                    water_amount=0,
                    garbage_amount=unit.property.garbage_charge,

                    month=month,
                    year=year
                )

            unit_bill.amount_expected = unit_bill.rent_amount + unit_bill.water_amount + unit_bill.garbage_amount
            unit_bill.save()

            unit_bill.update_amount_expected()

            GarbageBill.objects.create(
                unit=unit, 
                tenant=unit.tenant,
                amount_expected=unit.property.garbage_charge, 
                unit_bill=unit_bill,
                due_date=due_date

            )
        return redirect("garbage-bills")
    return render(request, "garbage_bills/new_garbage_bill.html")


def edit_garbage_bill(request, pk):
    if request.method == "POST":
        garbage_bill_id = request.POST.get("garbage_bill_id")
        amount_expected = request.POST.get("amount_expected")
        due_date = request.POST.get("due_date")

        garbage_bill = GarbageBill.objects.get(id=garbage_bill_id)
        garbage_bill.amount_expected = amount_expected
        garbage_bill.due_date = due_date
        garbage_bill.save()

        garbage_bill.unit_bill.garbage_amount = amount_expected
        garbage_bill.unit_bill.save()
        garbage_bill.unit_bill.update_amount_expected()


        return redirect("garbage-bills")


    return render(request, "garbage_bills/edit_garbage_bill.html")


def delete_garbage_bill(request, pk):
    if request.method == "POST":
        garbage_bill_id = request.POST.get("garbage_bill_id")
        garbage_bill = GarbageBill.objects.get(id=garbage_bill_id)
        garbage_bill.delete()
        return redirect("garbage-bills")

    return render(request, "garbage_bills/delete_garbage_bill.html")


# Garbage Bill Payments

class GarbageBillPaymentsView(ListView):
    model = GarbageBillPayment
    template_name = "garbage_bills/garbage_bill_payments.html"
    context_object_name = "garbage_bill_payments"

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
        context['payment_methods'] = PAYMENT_METHODS
        return context
                

def pay_garbage_bill(request):
    if request.method == "POST":
        garbage_bill_id = request.POST.get("garbage_bill_id")
        amount_paid = request.POST.get("amount_paid")
        payment_method = request.POST.get("payment_method")
        payment_date = request.POST.get("payment_date")

        garbage_bill = GarbageBill.objects.get(id=garbage_bill_id)
        GarbageBillPayment.objects.create(
            garbage_bill=garbage_bill,
            amount_paid=amount_paid,
            payment_method=payment_method,
            payment_date=payment_date
        )

        garbage_bill.amount_paid += Decimal(amount_paid)
        garbage_bill.save()


        if garbage_bill.amount_paid == garbage_bill.amount_expected:
            garbage_bill.status = PaymentStatuses.PAID.value
        elif garbage_bill.amount_paid < garbage_bill.amount_expected:
            garbage_bill.status = PaymentStatuses.PARTIALLY_PAID.value
        else:
            garbage_bill.status = PaymentStatuses.PENDING.value
        garbage_bill.save()

        garbage_bill.unit_bill.amount_paid += Decimal(amount_paid)
        garbage_bill.unit_bill.save()
        garbage_bill.unit_bill.update_amount_expected()


        return redirect("garbage-bills")
    return render(request, "garbage_bills/pay_garbage_bill.html")
