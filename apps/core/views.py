from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Any

from django.db.models import Sum, F
from django.db.models.functions import ExtractMonth, TruncMonth
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest

from apps.properties.models import Property, WaterBill, PropertyUnit, MaintenanceRequest
from apps.tenants.models import Tenant

# from apps.payments.models import WaterBill, TenantMonthlyBill
from apps.core.models import WaterPrice, Year, Month
from apps.payments.models import RentPayment, RentBill, UnitMonthBill, SecurityDeposit
from apps.core.constants import MONTHS_LIST, UserRoles, MaintenanceStatuses, PriorityLevels
import json
from django.http import JsonResponse
from django.views.decorators.http import require_GET


# Create your views here.
@login_required
def home(request: HttpRequest):
    if request.user.role == UserRoles.CARETAKER.value or request.user.role == UserRoles.HOUSE_MANAGER.value:
        return redirect("caretaker-dashboard")

    year = datetime.now().date().year
    print(f"Current Year: {year}")
    month_ids_list = list(
        RentBill.objects.filter(month__year__name=str(year))
        .values_list("month__id", flat=True)
        .distinct()
    )

    # Basic stats
    properties_count = Property.objects.count()
    tenants_count = Tenant.objects.all().count()

    # Get total revenue (sum of all paid rent)
    total_revenue = (
        RentBill.objects.filter(month__in=month_ids_list).aggregate(
            total=Sum("amount_paid")
        )["total"]
        or 0
    )

    # Get monthly revenue data for the last 6 months

    monthly_data = []
    if year:
        monthly_data = (
            RentBill.objects.filter(month__in=month_ids_list)
            .values("month")
            .annotate(
                expected_amount=Sum("amount_expected"), paid_amount=Sum("amount_paid")
            )
            .order_by("month__created_at")
        )

    # Format data for Chart.js
    labels = []
    expected_amounts = []
    paid_amounts = []

    for data in monthly_data:
        month = Month.objects.get(id=data["month"])
        labels.append(month.name)
        expected_amounts.append(float(data["expected_amount"] or 0))
        paid_amounts.append(float(data["paid_amount"] or 0))

    # Get occupancy data
    total_units = PropertyUnit.objects.count()
    occupied_units = PropertyUnit.objects.filter(is_occupied=True).count()
    vacant_units = total_units - occupied_units

    # Get recent activities
    recent_activities = []

    # Recent payments
    recent_payments = (
        RentBill.objects.filter(month__in=month_ids_list, status="paid")
        .select_related("tenant", "unit", "month")
        .order_by("-updated_at")[:3]
    )

    for payment in recent_payments:
        if payment.tenant and payment.tenant.user:
            tenant_label = payment.tenant.user.get_full_name() or payment.tenant.user.username
        else:
            tenant_label = "Tenant"
        unit_label = payment.unit.name if payment.unit else "Unit"
        month_label = payment.month.name if payment.month else ""
        recent_activities.append(
            {
                "type": "payment",
                "title": "New Payment Received",
                "description": f"{tenant_label} paid rent for {unit_label} ({month_label})",
                "timestamp": payment.updated_at,
                "icon_class": "fa-check",
                "bg_class": "success",
            }
        )

    # Sort activities by timestamp
    recent_activities.sort(key=lambda x: x["timestamp"], reverse=True)

    # Add available years for the filter
    # You might want to get this from your database
    current_year = datetime.now().year
    available_years = list(range(current_year - 3, current_year + 1))

    now = timezone.now()
    cal_month_name = now.strftime("%B")
    cal_year_name = str(now.date().year)
    current_month_obj = (
        Month.objects.filter(year__name=cal_year_name, name=cal_month_name)
        .select_related("year")
        .first()
    )

    unpaid_qs = UnitMonthBill.objects.filter(fully_paid=False)

    outstanding_total = unpaid_qs.aggregate(
        t=Sum(F("amount_expected") - F("amount_paid"))
    )["t"] or Decimal("0")
    tenants_unpaid_count = (
        unpaid_qs.exclude(tenant__isnull=True)
        .values("tenant_id")
        .distinct()
        .count()
    )

    collected_this_month = Decimal("0")
    home_bill_rows = []
    if current_month_obj:
        collected_this_month = (
            UnitMonthBill.objects.filter(month=current_month_obj, fully_paid=False).aggregate(
                s=Sum("amount_paid")
            )["s"]
            or Decimal("0")
        )
        unit_badge_tones = ("mint", "peach", "rose", "teal", "sage")
        for idx, ub in enumerate(
            UnitMonthBill.objects.filter(month=current_month_obj, fully_paid=False)
            .select_related("tenant__user", "unit")
            .order_by("unit__name")[:12]
        ):
            bal = ub.balance()
            if ub.tenant and ub.tenant.user:
                tname = (ub.tenant.user.get_full_name() or "").strip() or ub.tenant.user.username
            else:
                tname = "—"
            unit_label = ub.unit.name if ub.unit else "—"
            if ub.fully_paid:
                pay_status = "paid"
            elif ub.amount_paid and ub.amount_paid > 0:
                pay_status = "partial"
            else:
                pay_status = "unpaid"
            home_bill_rows.append(
                {
                    "unit_label": unit_label,
                    "property_name": ub.unit.property.name if ub.unit and ub.unit.property else "—",
                    "tenant_name": tname,
                    "period": f"{ub.month.name} {ub.month.year.name}" if ub.month and ub.month.year else "—",
                    "rent": ub.rent_amount,
                    "water": ub.water_amount,
                    "rent_balance": ub.rent_balance(),
                    "water_balance": ub.water_balance(),
                    "garbage_balance": ub.garbage_balance(),
                    "total": ub.amount_expected,
                    "status": pay_status,
                    "balance": bal,
                    "pk": ub.pk,
                    "unit_tone": unit_badge_tones[idx % len(unit_badge_tones)],
                }
            )

    open_repairs_qs = MaintenanceRequest.objects.exclude(
        status=MaintenanceStatuses.COMPLETED.value
    )
    open_repairs_count = open_repairs_qs.count()
    high_priority_repairs = open_repairs_qs.filter(
        priority=PriorityLevels.HIGH.value
    ).count()

    pending_deposits_qs = SecurityDeposit.objects.filter(fully_paid=False).select_related(
        "tenant__user"
    )
    pending_deposits_count = pending_deposits_qs.count()
    first_pending_deposit = pending_deposits_qs.first()

    def _deposit_summary(dep):
        if not dep:
            return None
        if dep.tenant and dep.tenant.user:
            nm = (dep.tenant.user.get_full_name() or "").strip() or dep.tenant.user.username
        else:
            nm = "Tenant"
        bal = dep.balance()
        return {"name": nm, "amount": bal}

    header_property = (
        Property.objects.filter(is_active=True).order_by("name").first()
    )

    context: Dict[str, Any] = {
        "properties_count": properties_count,
        "tenants_count": tenants_count,
        "total_revenue": f"KES {total_revenue:,.2f}",
        # Chart data
        "chart_data": {
            "labels": json.dumps(labels),
            "expected_amounts": json.dumps(expected_amounts),
            "paid_amounts": json.dumps(paid_amounts),
        },
        # Occupancy data
        "occupancy_data": {
            "occupied": occupied_units,
            "vacant": vacant_units,
            "total_units": total_units,
        },
        "recent_activities": recent_activities,
        "available_years": available_years,
        "current_year": current_year,
        "dashboard_period": now.strftime("%B %Y"),
        "dashboard_property_name": header_property.name if header_property else "All properties",
        "tenants_unpaid_count": tenants_unpaid_count,
        "outstanding_total": outstanding_total,
        "collected_this_month": collected_this_month,
        "open_repairs_count": open_repairs_count,
        "high_priority_repairs": high_priority_repairs,
        "pending_deposits_count": pending_deposits_count,
        "first_pending_deposit": _deposit_summary(first_pending_deposit),
        "home_bill_rows": home_bill_rows,
        "has_current_month_bills": bool(current_month_obj),
    }
    return render(request, "home.html", context)


@login_required
def caretaker_dashboard(request: HttpRequest):
    rent_bills = RentBill.objects.exclude(fully_paid=True).order_by("-created_at")
    water_bills = WaterBill.objects.exclude(
        status__in=[MaintenanceStatuses.COMPLETED.value, MaintenanceStatuses.PAID.value]
    ).order_by("-created_at")

    total_rent = RentBill.objects.aggregate(total_amount=Sum("amount_expected"))["total_amount"]
    total_water = WaterBill.objects.aggregate(total_amount=Sum("amount"))["total_amount"]

    total_rent_paid = RentBill.objects.aggregate(total_amount=Sum("amount_paid"))["total_amount"]
    total_water_paid = WaterBill.objects.aggregate(total_amount=Sum("amount_paid"))["total_amount"]

    total_rent_due = 0
    total_water_due = 0

    if total_rent and total_rent_paid:
        total_rent_due = total_rent - total_rent_paid

    if total_water and total_water_paid:
        total_water_due = total_water - total_water_paid

    context: Dict[str, Any] = {
        "rent_bills": rent_bills[:5],
        "water_bills": water_bills[:5],
        "bill_months": MONTHS_LIST,
        "years": Year.objects.filter(is_active=True).order_by("-created_at"),
        "months": MONTHS_LIST,
        "properties": Property.objects.filter(is_active=True).order_by("-created_at"),
        "total_rent_due": round(total_rent_due, 0) if total_rent_due is not None else 0,
        "total_water_due": (
            round(total_water_due, 0) if total_water_due is not None else 0
        ),
        "units": PropertyUnit.objects.filter(is_occupied=True).order_by("-created_at"),
    }
    return render(request, "caretaker_dashboard.html", context)


@login_required
def years(request: HttpRequest):
    years = Year.objects.all().order_by("-created_at")
    context = {"years": years}
    return render(request, "settings/years.html", context)


@login_required
def new_year(request: HttpRequest):
    if request.method == "POST":
        name = request.POST.get("name")

        if Year.objects.filter(name=name).exists():
            return redirect("years")

        year = Year.objects.create(name=name)

        for month in MONTHS_LIST:
            Month.objects.create(name=month, year=year)

        return redirect("years")
    return render(request, "settings/new_year.html")


@login_required
def deactivate_year(request: HttpRequest, id: int):
    year = Year.objects.get(id=id)
    year.is_active = False
    year.months.update(is_active=False)
    year.save()
    return redirect("years")


@login_required
def activate_year(request: HttpRequest, id: int):
    year = Year.objects.get(id=id)
    year.is_active = True
    year.months.update(is_active=True)
    year.save()
    return redirect("years")


@login_required
def months(request: HttpRequest):
    months = Month.objects.all().order_by("-created_at")
    context = {"months": months}
    return render(request, "settings/months.html", context)


@login_required
def water_prices(request: HttpRequest):
    water_prices = WaterPrice.objects.all().order_by("-created_at")
    context = {"water_prices": water_prices}
    return render(request, "settings/water_prices.html", context)


@login_required
def edit_water_price(request: HttpRequest):
    if request.method == "POST":
        water_price_id = request.POST.get("water_price_id")
        unit_price = request.POST.get("unit_price")

        WaterPrice.objects.filter(id=water_price_id).update(unit_price=unit_price)
        return redirect("water-prices")
    return render(request, "settings/edit_water_price.html")


@require_GET
def chart_data_api(request: HttpRequest):
    """API endpoint to get chart data for a specific year"""
    year = request.GET.get("year", datetime.now().year)
    try:
        year = int(year)
    except ValueError:
        year = datetime.now().year

    # Get revenue data for the selected year
    # This is just an example - adjust according to your actual data structure
    revenue_data = get_revenue_data_for_year(year)

    # Get occupancy data for the selected year
    occupancy_data = get_occupancy_data_for_year(year)

    # Calculate total revenue for the selected year
    total_revenue = calculate_total_revenue_for_year(year)

    return JsonResponse(
        {
            "revenue": revenue_data,
            "occupancy": occupancy_data,
            "total_revenue": f"Kes {total_revenue:,.2f}",  # Format as currency
        }
    )


def get_revenue_data_for_year(year):
    # Get monthly data for the specified year

    # Get all months for the specified year
    months_list = list(
        RentBill.objects.filter(month__year__name=str(year))
        .values_list("month__id", flat=True)
        .distinct()
    )

    monthly_data = (
        RentBill.objects.filter(month__in=months_list)
        .values("month")
        .annotate(
            expected_amount=Sum("amount_expected"), paid_amount=Sum("amount_paid")
        )
        .order_by("month__created_at")
    )

    labels = []
    expected_amounts = []
    paid_amounts = []

    # Only process months that have RentBill records
    # This is already happening since we're iterating over the query results
    for data in monthly_data:
        month = Month.objects.get(id=data["month"])
        labels.append(month.name)
        expected_amounts.append(float(data["expected_amount"] or 0))
        paid_amounts.append(float(data["paid_amount"] or 0))

    return {
        "labels": labels,
        "expected_amounts": expected_amounts,
        "paid_amounts": paid_amounts,
    }


def get_occupancy_data_for_year(year):
    # Implement logic to get occupancy data for the specified year
    # Example:
    occupied_units = PropertyUnit.objects.filter(is_occupied=True).count()
    total_units = PropertyUnit.objects.all().count()
    vacant_units = total_units - occupied_units
    return {
        "occupied": occupied_units,  # Number of occupied units for the selected year
        "vacant": vacant_units,  # Number of vacant units for the selected year
    }


def calculate_total_revenue_for_year(year):
    # Your logic to calculate total revenue for the given year
    # For example:

    total = (
        RentBill.objects.filter(year__name=str(year)).aggregate(Sum("amount_paid"))[
            "amount_paid__sum"
        ]
        or 0
    )

    return total
