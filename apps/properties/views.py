from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required

from django.db.models import Avg
from datetime import datetime
from decimal import Decimal
from django.views.generic import ListView
from django.http import HttpRequest, JsonResponse
from django.db.models import Q
from django.db import transaction
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin

from apps.properties.models import Property, PropertyUnit, MaintenanceRequest, WaterBill
from apps.core.models import Month, Year, UserAction
from apps.tenants.models import Tenant
from apps.payments.models import RentPayment, RentBill
from apps.users.models import User

from apps.core.constants import (
    UNIT_TYPES,
    UNIT_STATUSES,
    GENDER_LIST,
    MONTHS_LIST,
    PAYMENT_METHODS,
)

# Create your views here.

years = Year.objects.filter(is_active=True)


@login_required
def properties(request):
    properties = Property.objects.all().order_by("-created_at")
    house_managers = User.objects.filter(
        role__in=["Landlord", "House Manager", "Caretaker"]
    )
    context = {
        "properties": properties,
        "gender_choices": GENDER_LIST,
        "house_managers": house_managers,
    }
    return render(request, "properties/properties.html", context)


MONTHS = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]


@login_required
def property_detail(request, id):
    property = get_object_or_404(Property, id=id)
    all_units = PropertyUnit.objects.filter(property=property).order_by('name')
    
    # Paginate units (7 per page)
    paginator = Paginator(all_units, 7)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    maintenance_requests = MaintenanceRequest.objects.filter(
        unit__property=property, status="Pending"
    ).count()

    unit_numbers = [unit.name for unit in page_obj.object_list]

    rent_data = {unit: {month: "Unpaid" for month in MONTHS} for unit in unit_numbers}

    bills = RentBill.objects.filter(unit__property=property).filter(
        year__name=str(2025)
    )
    for bill in bills:
        month_name = bill.month.name
        if month_name in MONTHS and bill.unit.name in rent_data:
            status = (
                "Fully Paid"
                if bill.fully_paid
                else ("Partially Paid" if bill.amount_paid > 0 else "Unpaid")
            )
            rent_data[bill.unit.name][month_name] = status

    # Generate rows for the table using only the units on this page
    rows = []
    for unit in unit_numbers:
        row = [unit] + [rent_data[unit][month] for month in MONTHS]
        rows.append(row)

    occupied_units = all_units.filter(is_occupied=True).count()
    tenants = Tenant.objects.all()
    house_managers = User.objects.filter(
        role__in=["House Manager", "Landlord", "Caretaker"]
    )

    context = {
        "property": property,
        "units": page_obj,
        "page_obj": page_obj,
        "unit_numbers": unit_numbers,
        "months": MONTHS,
        "rows": rows,
        "maintenance_requests": maintenance_requests,
        "occupied_units": occupied_units,
        "tenants": tenants,
        "house_managers": house_managers,
        "unit_types": UNIT_TYPES,
        "unit_statuses": UNIT_STATUSES
    }
    return render(request, "properties/property_details.html", context)


@login_required
def new_property(request):
    house_managers = User.objects.filter(
        role__in=["Landlord", "House Manager", "Caretaker"]
    )
    if request.method == "POST":
        owner = request.user
        name = request.POST.get("name")
        address = request.POST.get("address")
        city = request.POST.get("city")

        country = request.POST.get("country")
        units = request.POST.get("units")
        house_manager = request.POST.get("house_manager")
        
        user = User.objects.get(id=house_manager)

        garbage_charge = request.POST.get("garbage_charge")
        water_charge = request.POST.get("water_charge")
        Property.objects.create(
            owner=owner,
            name=name,
            garbage_charge=garbage_charge,
            water_charge=water_charge,
            address=address,
            city=city,
            country=country,
            units=units,
            is_active=True,
            house_manager=user,
        )
        UserAction.objects.create(
            user=request.user,
            action=f"Created property '{name}'",
            action_type="Create",
            description=f"Created property '{name}'",
        )
        return redirect("properties")
    return render(request, "properties/new_property.html", {"house_managers": house_managers})



@login_required
def edit_property(request):
    current_property = Property.objects.filter(id=request.GET.get("id")).first()
    if request.method == "POST":
        property_id = request.POST.get("property_id")
        name = request.POST.get("name")
        address = request.POST.get("address")
        city = request.POST.get("city")
        country = request.POST.get("country")
        units = request.POST.get("units")
        garbage_charge = request.POST.get("garbage_charge")
        water_charge = request.POST.get("water_charge")

        house_manager = request.POST.get("house_manager")
        user = User.objects.get(id=house_manager)

        property = Property.objects.get(id=property_id)

        property.name = name
        property.garbage_charge = garbage_charge
        property.water_charge = water_charge
        property.address = address
        property.city = city
        property.country = country
        property.units = units
        property.house_manager = user
        property.save()
        UserAction.objects.create(
            user=request.user,
            action=f"Edited property '{name}'",
            action_type="Update",
            description=f"Edited property '{name}'",
        )
        return redirect(f"/properties/{property_id}")
    return render(request, "properties/edit_property.html", {"property": current_property, "house_managers": User.objects.filter(role__in=["Landlord", "House Manager", "Caretaker"])})


@login_required
def delete_property(request):
    if request.method == "POST":
        property_id = request.POST.get("property_id")
        property = Property.objects.get(id=property_id)
        UserAction.objects.create(
            user=request.user,
            action=f"Deleted property '{property.name}'",
            action_type="Delete",
            description=f"Deleted property '{property.name}'",
        )
        property.delete()
        return redirect("properties")
    return render(request, "properties/delete_property.html")


class PropertyUnitListView(LoginRequiredMixin, ListView):
    model = PropertyUnit
    template_name = "properties/units/units.html"
    context_object_name = "units"
    paginate_by = 9

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query)
                | Q(name__icontains=search_query)
                | Q(property__name__icontains=search_query)
            )

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("search", "")
        context["tenants"] = Tenant.objects.all()
        return context


@login_required
def property_unit_detail(request: HttpRequest, id: int):
    unit = PropertyUnit.objects.get(id=id)

    # Get all data
    all_maintenance_requests = MaintenanceRequest.objects.filter(unit=unit).order_by(
        "-created_at"
    )
    all_water_bills = unit.unitwaterbills.all().order_by("-created_at")
    all_payments = RentPayment.objects.filter(rent_bill__unit=unit).order_by(
        "-created_at"
    )

    # Paginate maintenance requests - 10 items per page
    maintenance_paginator = Paginator(all_maintenance_requests, 5)
    maintenance_page = request.GET.get("maintenance_page", 1)
    maintenance_requests = maintenance_paginator.get_page(maintenance_page)

    # Paginate water bills - 10 items per page
    water_bills_paginator = Paginator(all_water_bills, 5)
    water_bills_page = request.GET.get("water_bills_page", 1)
    water_bills = water_bills_paginator.get_page(water_bills_page)

    # Paginate payments - 10 items per page
    payments_paginator = Paginator(all_payments, 5)
    payments_page = request.GET.get("payments_page", 1)
    payments = payments_paginator.get_page(payments_page)

    # Calculate statistics
    average_water_bill = all_water_bills.aggregate(avg_amount=Avg("amount"))[
        "avg_amount"
    ]
    maintenance_cost = sum(
        list(all_maintenance_requests.values_list("cost", flat=True))
    )
    total_rent = all_payments.aggregate(total_amount=Avg("amount_paid"))["total_amount"]

    monthly_bills = unit.unitmonthbills.all().order_by("-created_at")

    free_tenants = Tenant.objects.filter(tenantunit__isnull=True)
    print(f"Free Tenants: {free_tenants}")

    context = {
        "unit": unit,
        "maintenance_requests": maintenance_requests,
        "water_bills": water_bills,
        "payments": payments,
        "average_water_bill": round(average_water_bill, 2) if average_water_bill else 0,
        "maintenance_cost": round(maintenance_cost, 2) if maintenance_cost else 0,
        "unit_statuses": UNIT_STATUSES,
        "total_rent": round(total_rent, 2) if total_rent else 0,
        "monthly_bills": monthly_bills,
        "free_tenants": free_tenants,
    }
    return render(request, "properties/units/unit_details.html", context)


@login_required
def new_property_unit(request: HttpRequest):
    property = Property.objects.filter(id=request.GET.get("property_id")).first()
    if request.method == "POST":
        property_id = request.POST.get("property_id")
        name = request.POST.get("unit_number")
        rent = request.POST.get("rent")
        unit_type = request.POST.get("unit_type")
        status = request.POST.get("status")
        floor = request.POST.get("floor")
        security_deposit = request.POST.get("security_deposit")
        water_price = request.POST.get("water_price")

        unit = PropertyUnit.objects.create(
            property_id=property_id,
            name=name,
            water_price=water_price,
            rent=rent,
            unit_type=unit_type,
            status=status,
            is_occupied=True if status == "Occupied" else False,
            floor=floor,
            security_deposit=security_deposit,
        )
        UserAction.objects.create(
            user=request.user,
            action=f"Created unit '{unit.name}'",
            action_type="Created",
            description=f"Created unit '{unit.name}' in property '{unit.property.name}'"
        )

        return redirect("property-detail", id=property_id)
    return render(request, "properties/units/new_unit.html", {"property": property})


@login_required
def edit_property_unit(request: HttpRequest):
    unit = PropertyUnit.objects.filter(id=request.GET.get("unit_id")).first()
    if request.method == "POST":
        
        unit_id = request.GET.get("unit_id")
        name = request.POST.get("unit_number")
        rent = request.POST.get("rent")
        unit_type = request.POST.get("unit_type")
        status = request.POST.get("status")
        floor = request.POST.get("floor")
        security_deposit = request.POST.get("security_deposit")
        water_price = request.POST.get("water_price")

        print(f"Unit ID: {request.GET.get("unit_id")}")

        unit = PropertyUnit.objects.get(id=unit_id)
        unit.name = name
        unit.rent = rent
        unit.unit_type = unit_type
        unit.status = status
        unit.floor = floor
        unit.water_price = water_price
        unit.is_occupied = True if status == "Occupied" else False
        unit.security_deposit = security_deposit
        unit.save()

        UserAction.objects.create(
            user=request.user,
            action=f"Edited unit '{name}'",
            action_type="Updated",
            description=f"Edited unit '{name}' in property '{unit.property.name}'"
        )

        return redirect("unit-detail", id=unit.id)
    return render(request, "properties/units/edit_unit.html", {"unit": unit, "unit_types": UNIT_TYPES, "statuses": UNIT_STATUSES})


@login_required
def delete_property_unit(request: HttpRequest):
    if request.method == "POST":
        unit_id = request.POST.get("unit_id")
        unit = PropertyUnit.objects.get(id=unit_id)
        UserAction.objects.create(
            user=request.user,
            action=f"Deleted unit '{unit.name}'",
            action_type="Deleted",
            description=f"Deleted unit '{unit.name}' from property '{unit.property.name}'"
        )
        unit.delete()
        return redirect("units")
    return render(request, "properties/units/delete_unit.html")


@login_required
def assign_tenant(request: HttpRequest):
    if request.method == "POST":
        unit_id = request.POST.get("unit_id")
        tenant_id = request.POST.get("tenant_id")
        unit = PropertyUnit.objects.get(id=unit_id)
        tenant = Tenant.objects.get(id=tenant_id)
        unit.tenant = tenant
        unit.is_occupied = True
        unit.status = "Occupied"
        unit.save()
        UserAction.objects.create(
            user=request.user,
            action=f"Assigned tenant",
            action_type="Update",
            description=f"Assigned tenant '{tenant.user.first_name} {tenant.user.last_name}' to unit '{unit.name}' in property '{unit.property.name}'"
        )
        return redirect("unit-detail", id=unit_id)
    return render(request, "properties/units/set_tenant.html")


@login_required
def remove_tenant(request: HttpRequest):
    if request.method == "POST":
        unit_id = request.POST.get("unit_id")
        unit = PropertyUnit.objects.get(id=unit_id)
        unit.tenant = None
        unit.is_occupied = False
        unit.status = "Vacant"
        unit.save()
        UserAction.objects.create(
            user=request.user,
            action=f"Removed tenant",
            action_type="Create",
            description=f"Tenant Removed from unit '{unit.name}' in property '{unit.property.name}'"
        )
        return redirect("unit-detail", id=unit_id)
    return render(request, "properties/units/remove_tenant.html")


def get_units_by_property(request: HttpRequest):
    property_id = request.GET.get("property_id")
    if property_id:
        units = PropertyUnit.objects.filter(property_id=property_id)
        data = [{"id": unit.id, "name": unit.name} for unit in units]
        return JsonResponse({"units": data})
    return JsonResponse({"units": []})
