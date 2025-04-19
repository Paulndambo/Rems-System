from datetime import datetime
import math
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.db.models import Q
from django.db import transaction
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin

from apps.properties.models import PropertyUnit, WaterBill
from apps.core.models import Month, Year
from apps.payments.models import RentBill, UnitMonthBill, GarbageBill
from apps.core.constants import MONTHS_LIST, PAYMENT_METHODS


# Create your views here.
"""Water Bills"""
class WaterBillListView(LoginRequiredMixin, ListView):
    model = WaterBill
    template_name = "water_bills/bills.html"
    context_object_name = "water_bills"
    paginate_by = 9

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        print(f"You are searching for {search_query}")

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query)
                | Q(unit__name__icontains=search_query)
                | Q(month__name__icontains=search_query)
                | Q(year__name__icontains=search_query)
                | Q(tenant__user__first_name__icontains=search_query)
                | Q(tenant__user__last_name__icontains=search_query)
            )

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("search", "")
        context["months"] = MONTHS_LIST
        context["years"] = Year.objects.filter(is_active=True)
        context["payment_methods"] = PAYMENT_METHODS
        context["units"] = PropertyUnit.objects.filter(is_occupied=True).order_by("-created_at")
        return context


@login_required
@transaction.atomic
def new_water_bill(request):
    if request.method == "POST":
        unit_id = request.POST.get('unit')
        
        year_id = request.POST.get('year')
        month_name = request.POST.get('month')
        previous_reading = request.POST.get('previous_reading')
        current_reading = request.POST.get('current_reading')
        units_consumed = Decimal(current_reading) - Decimal(previous_reading)

        unit = PropertyUnit.objects.get(id=unit_id)
        year = Year.objects.get(id=year_id)
        month = Month.objects.get(name=month_name, year=year)

        unit_bill = UnitMonthBill.objects.filter(unit=unit, month=month, year=year).first()

        water_cost = (Decimal(unit.water_price) * Decimal(units_consumed))
        water_cost_rounded_off = math.ceil(water_cost)

        if not unit_bill:
            unit_bill = UnitMonthBill.objects.create(
                unit=unit,
                tenant=unit.tenant,
                month=month,
                year=year
            )

        unit_bill.water_amount = water_cost_rounded_off
        unit_bill.update_amount_expected()
        unit_bill.save()

        water_bill = WaterBill.objects.create(
            unit_bill=unit_bill,
            unit=unit,
            property=unit.property,
            tenant=unit.tenant,
            year=year,
            month=month,
            previous_reading=previous_reading,
            current_reading=current_reading,
            meter_number=unit.water_meter_number,
            units_consumed=units_consumed,
            amount=water_cost_rounded_off
        )
        
        rent_bill = RentBill.objects.filter(unit=unit, unit_bill=unit_bill).first()
        if not rent_bill:
            RentBill.objects.create(
                unit=unit,
                unit_bill=unit_bill,
                tenant=unit.tenant,
                amount_expected=unit.rent,
                due_date=water_bill.due_date,
                month=month,
                year=year
            )

        unit_bill.update_amount_expected()
        unit_bill.save()

        garbage_bill = GarbageBill.objects.filter(unit=unit, unit_bill=unit_bill).first()
        if not garbage_bill:
            GarbageBill.objects.create(
                unit=unit,
                unit_bill=unit_bill,
                tenant=unit.tenant,
                amount_expected=unit.property.garbage_charge,
                due_date=water_bill.due_date,
            )

        unit_bill.rent_amount = unit.rent
        unit_bill.garbage_amount = unit.property.garbage_charge   
        unit_bill.update_amount_expected()
        unit_bill.save()

        return redirect("water-bills")

    return render(request, 'water_bills/new_water_bill.html')



@login_required
def view_water_bill(request, id):
    water_bill = WaterBill.objects.get(id=id)
    date_today = datetime.now().strftime("%Y-%m-%d")
    return render(request, 'water_bills/view_bill.html', {'bill': water_bill, 'date_today': date_today})


@login_required
def edit_water_bill(request):
    if request.method == "POST":
        water_bill_id = request.POST.get('water_bill_id')
    

        previous_reading = request.POST.get('previous_reading')
        current_reading = request.POST.get('current_reading')
        reading_date = request.POST.get('reading_date')
        units_consumed = Decimal(current_reading) - Decimal(previous_reading)

        month_name = request.POST.get('month')
        year_id = request.POST.get('year')

        year = Year.objects.get(id=year_id)
        month = Month.objects.get(name=month_name, year=year)

        water_bill = WaterBill.objects.get(id=water_bill_id)
        water_bill.previous_reading = previous_reading
        water_bill.current_reading = current_reading
        water_bill.units_consumed = units_consumed
        water_bill.month = month
        water_bill.year = year
        water_bill.reading_date = reading_date
        water_bill.save()


        water_cost = (Decimal(water_bill.unit.water_price) * Decimal(units_consumed))
        water_cost_rounded_off = math.ceil(water_cost)
        water_bill.amount = water_cost_rounded_off
        water_bill.save()

        water_bill.unit_bill.water_amount = water_cost_rounded_off
        water_bill.unit_bill.update_amount_expected()
        water_bill.unit_bill.save()

        return redirect("water-bills")
    return render(request, 'water_bills/edit_bill.html')


@login_required
def delete_water_bill(request):
    if request.method == "POST":
        water_bill_id = request.POST.get('water_bill_id')
        WaterBill.objects.get(id=water_bill_id).delete()
        return redirect("water-bills")
    return render(request, 'water_bills/delete_bill.html')