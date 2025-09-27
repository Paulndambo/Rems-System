from datetime import datetime
import math
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from decimal import Decimal
from django.db.models import Q
from django.db import transaction
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages

from apps.properties.models import PropertyUnit, WaterBill
from apps.core.models import Month, Year
from apps.payments.models import RentBill, UnitMonthBill, GarbageBill
from apps.core.constants import MONTHS_LIST, PAYMENT_METHODS


from apps.properties.water_bills.billing_mixin import TenantBillingMixin

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
        context["units"] = PropertyUnit.objects.filter(is_occupied=True).order_by(
            "-created_at"
        )
        return context


@login_required
@transaction.atomic
def new_water_bill(request):
    if request.method == "POST":
        unit_id = request.POST.get("unit")
        unit = PropertyUnit.objects.get(id=unit_id)

        last_water_bill = (
            WaterBill.objects.filter(unit=unit).order_by("-created_at").first()
        )

        previous_reading = last_water_bill.current_reading if last_water_bill else 0

        year_id = request.POST.get("year")
        month_name = request.POST.get("month")
        current_reading = request.POST.get("current_reading")

        year = Year.objects.get(id=year_id)
        month = Month.objects.get(name=month_name, year=year)

        try:
            biller = TenantBillingMixin(
                year=year,
                month=month,
                previous_reading=previous_reading,
                current_reading=current_reading,
                unit=unit,
            )
            res = biller.generate_bill()
            messages.success(
                request, "You have successfully generated monthly bill for James!!"
            )
        except Exception as e:
            raise e

        return redirect("water-bills")
    return render(request, "water_bills/new_water_bill.html")


@login_required
def view_water_bill(request, id):
    water_bill = WaterBill.objects.get(id=id)
    date_today = datetime.now().strftime("%Y-%m-%d")
    return render(
        request,
        "water_bills/view_bill.html",
        {"bill": water_bill, "date_today": date_today},
    )


@login_required
def edit_water_bill(request):
    if request.method == "POST":
        water_bill_id = request.POST.get("water_bill_id")
        water_bill = WaterBill.objects.get(id=water_bill_id)

        previous_reading = water_bill.previous_reading

        current_reading = request.POST.get("current_reading")
        reading_date = request.POST.get("reading_date")
        units_consumed = Decimal(current_reading) - Decimal(previous_reading)

        month_name = request.POST.get("month")
        year_id = request.POST.get("year")

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

        water_bill.refresh_bill()

        water_cost = Decimal(water_bill.unit.water_price) * Decimal(units_consumed)
        water_cost_rounded_off = math.ceil(water_cost)
        water_bill.amount = water_cost_rounded_off
        water_bill.save()

        water_bill.unit_bill.water_amount = water_cost_rounded_off
        water_bill.unit_bill.update_amount_expected()
        water_bill.unit_bill.save()

        return redirect("water-bills")
    return render(request, "water_bills/edit_bill.html")


@login_required
def delete_water_bill(request):
    if request.method == "POST":
        water_bill_id = request.POST.get("water_bill_id")
        WaterBill.objects.get(id=water_bill_id).delete()
        return redirect("water-bills")
    return render(request, "water_bills/delete_bill.html")
