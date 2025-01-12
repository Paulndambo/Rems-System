from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Avg

from django.views.generic import ListView
from django.http import JsonResponse
from django.db.models import Q

from apps.properties.models import Property, PropertyUnit, MaintenanceRequest, WaterBill
from apps.core.models import Month, Year
from apps.tenants.models import Tenant
from apps.payments.models import TenantPayment, RentPayment
from apps.core.constants import UNIT_TYPES, UNIT_STATUSES, GENDER_LIST, MONTHS_LIST, PAYMENT_METHODS
# Create your views here.

years = Year.objects.filter(is_active=True)
@login_required
def properties(request):
    properties = Property.objects.all()
    context = {
        "properties": properties,
        "gender_choices": GENDER_LIST
    }
    return render(request, 'properties/properties.html', context)


@login_required
def property_detail(request, id):
    property = Property.objects.get(id=id)
    units = PropertyUnit.objects.filter(property=property)

    maintenance_requests = MaintenanceRequest.objects.filter(unit__property=property, status="Pending").count()
    context = {
        'property': property,
        'units': units,
        "unit_types": UNIT_TYPES,
        "unit_statuses": UNIT_STATUSES,
        "maintenance_requests": maintenance_requests
    }
    return render(request, 'properties/property_details.html', context)


@login_required
def new_property(request):
    if request.method == "POST":
        owner = request.user
        name = request.POST.get('name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        
        country = request.POST.get('country')
        units = request.POST.get('units')

        manager_name = request.POST.get('manager_name')
        manager_email = request.POST.get('manager_email')
        manager_phone = request.POST.get('manager_phone')
        manager_gender = request.POST.get('manager_gender')
        
        Property.objects.create(
            owner=owner, 
            name=name, 
            address=address, 
            city=city, 
            country=country, 
            units=units,
            manager_name=manager_name,
            manager_email=manager_email,
            manager_gender=manager_gender,
            manager_phone_number=manager_phone,
            is_active=True
        )
        return redirect("properties")
    return render(request, 'properties/new_property.html')


@login_required
def edit_property(request):
    if request.method == "POST":
        property_id = request.POST.get('property_id')
        name = request.POST.get('name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        country = request.POST.get('country')
        units = request.POST.get('units')

        manager_name = request.POST.get('manager_name')
        manager_email = request.POST.get('manager_email')
        manager_phone = request.POST.get('manager_phone')
        manager_gender = request.POST.get('manager_gender')
       
        
        Property.objects.filter(id=property_id).update(
            name=name, 
            address=address, 
            city=city, 
            country=country, 
            units=units,
            manager_name=manager_name,
            manager_email=manager_email,
            manager_phone_number=manager_phone,
            manager_gender=manager_gender
        )
        return redirect(f"/properties/{property_id}")
    return render(request, 'properties/edi_property.html')


@login_required
def delete_property(request):
    if request.method == "POST":
        property_id = request.POST.get('property_id')
        Property.objects.get(id=property_id).delete()
        return redirect("properties")
    return render(request, 'properties/delete_property.html')


@login_required
def property_units(request):
    units = PropertyUnit.objects.all().order_by("-created_at")
    tenants = Tenant.objects.all()

    context = {
        "units": units,
        "tenants": tenants
    }

    return render(request, 'properties/units/units.html', context)


@login_required
def property_unit_detail(request, id):
    unit = PropertyUnit.objects.get(id=id)

    maintenance_requests = MaintenanceRequest.objects.filter(unit=unit)
    water_bills = unit.unitwaterbills.all().order_by('-created_at')

    average_water_bill = water_bills.aggregate(avg_amount=Avg('amount'))['avg_amount']
    maintenance_cost = sum(list(maintenance_requests.values_list('cost', flat=True)))

    payments = RentPayment.objects.filter(rent_bill__unit=unit)
    total_rent = RentPayment.objects.filter(rent_bill__unit=unit).aggregate(total_amount=Avg('amount_paid'))['total_amount']

    context = {
        'unit': unit,
        'maintenance_requests': maintenance_requests,
        'water_bills': water_bills,
        "average_water_bill": average_water_bill if average_water_bill else 0,
        "maintenance_cost": maintenance_cost,
        "unit_statuses": UNIT_STATUSES,
        "payments": payments,
        "total_rent": round(total_rent, 0) if total_rent else 0
    }
    return render(request, 'properties/units/unit_details.html', context)


@login_required
def new_property_unit(request):
    if request.method == "POST":
        property_id = request.POST.get('property_id')

        property = Property.objects.get(id=property_id)
        name = request.POST.get('unit_number')
        rent = request.POST.get('rent')
        size = request.POST.get('size')
        unit_type = request.POST.get('unit_type')
        status = request.POST.get('status')
        floor = request.POST.get('floor')
        security_deposit = request.POST.get('security_deposit')
        
        PropertyUnit.objects.create(
            property=property, 
            name=name, 
            rent=rent, 
            size=size,
            unit_type=unit_type,
            status=status,
            is_occupied=True if status == "Occupied" else False,
            floor=floor,
            security_deposit=security_deposit
        )
        return redirect("property-detail", id=property_id)
    return render(request, 'properties/units/new_unit.html')


@login_required
def edit_property_unit(request):
    if request.method == "POST":
        unit_id = request.POST.get('unit_id')
        name = request.POST.get('unit_number')
        rent = request.POST.get('rent')
        size = request.POST.get('size')
        unit_type = request.POST.get('unit_type')
        status = request.POST.get('status')
        floor = request.POST.get('floor')
        security_deposit = request.POST.get('security_deposit')

        unit=PropertyUnit.objects.get(id=unit_id)
        unit.name=name 
        unit.rent=rent 
        unit.size=size
        unit.unit_type=unit_type
        unit.status=status
        unit.floor=floor
        unit.is_occupied=True if status == "Occupied" else False
        unit.security_deposit=security_deposit
        unit.save()
        
        return redirect("unit-detail", id=unit.id)
    return render(request, 'properties/units/edit_unit.html')


@login_required
def delete_property_unit(request):
    if request.method == "POST":
        unit_id = request.POST.get('unit_id')
        unit = PropertyUnit.objects.get(id=unit_id)
        unit.delete()
        return redirect("units")
    return render(request, 'properties/units/delete_unit.html')


@login_required
def assign_tenant(request):
    if request.method == "POST":
        unit_id = request.POST.get('unit_id')
        tenant_id = request.POST.get('tenant')
        unit = PropertyUnit.objects.get(id=unit_id)
        tenant = Tenant.objects.get(id=tenant_id)
        unit.tenant = tenant
        unit.is_occupied = True
        unit.status = "Occupied"
        unit.save()
        return redirect("unit-detail", id=unit.id)
    return render(request, 'properties/units/assign_tenant.html')

"""Maintenance Requests"""
@login_required
def maintenance_requests(request):
    maintenance_requests = MaintenanceRequest.objects.all().order_by("-created_at")
    units = PropertyUnit.objects.all().order_by("-created_at")

    priority_levels = ["High", "Medium", "Low"]
    maintenance_statuses = ["Pending", "In Progress", "Completed"]

    context = {
        "maintenance_requests": maintenance_requests,
        "units": units,
        "priority_levels": priority_levels,
        "maintenance_statuses": maintenance_statuses
    }
    return render(request, 'properties/maintenance_requests/maintenance_requests.html', context)


@login_required
def new_maintenance_request(request):
    if request.method == "POST":
        unit_id = request.POST.get('unit')
        unit = PropertyUnit.objects.get(id=unit_id)

        title = request.POST.get('title')
        priority = request.POST.get('priority')
        description = request.POST.get('description')

        MaintenanceRequest.objects.create(
            title=title,
            property=unit.property, 
            unit=unit, 
            description=description,
            priority=priority
        )
        return redirect("unit-detail", id=unit_id)
    return render(request, 'properties/maintenance_requests/new_maintenance_request.html')


@login_required
def edit_maintenance_request(request):
    if request.method == "POST":
        maintenance_request_id = request.POST.get('request_id')
        title = request.POST.get('title')
        description = request.POST.get('description')
        status = request.POST.get('status')
       
        priority = request.POST.get('priority')
        cost = request.POST.get('cost')

        maintenance_request = MaintenanceRequest.objects.get(id=maintenance_request_id)
        maintenance_request.title = title
        maintenance_request.description = description
        maintenance_request.status = status
        maintenance_request.priority = priority
        maintenance_request.cost = cost
        maintenance_request.save()
        return redirect("maintenance-requests")
    return render(request, 'properties/maintenance_requests/edit_maintenance_request.html')


@login_required
def delete_maintenance_request(request):
    if request.method == "POST":
        maintenance_request_id = request.POST.get('request_id')
        MaintenanceRequest.objects.get(id=maintenance_request_id).delete()
        return redirect("maintenance-requests")
    return render(request, 'properties/maintenance_requests/delete_maintenance_request.html')


"""Water Bills"""
class WaterBillListView(ListView):
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
            )

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("search", "")
        context["months"] = MONTHS_LIST
        context["years"] = years
        context["payment_methods"] = PAYMENT_METHODS
        context["units"] = PropertyUnit.objects.filter(is_occupied=True).order_by("-created_at")
        return context

@login_required
def water_bills(request):
    water_bills = WaterBill.objects.all().order_by("-created_at")

    units = PropertyUnit.objects.filter(is_occupied=True).order_by("-created_at")

    context = {
        "water_bills": water_bills,
        "months": MONTHS_LIST,
        "years": years,
        "units": units
    }
    return render(request, 'water_bills/bills.html', context)


@login_required
def new_water_bill(request):
    if request.method == "POST":
        unit_id = request.POST.get('unit')
        
        year_id = request.POST.get('year')
        month_name = request.POST.get('month')
        previous_balance = request.POST.get('previous_balance')
        previous_reading = request.POST.get('previous_reading')
        current_reading = request.POST.get('current_reading')

        unit = PropertyUnit.objects.get(id=unit_id)
        year = Year.objects.get(id=year_id)
        month = Month.objects.get(name=month_name, year=year)

        print(previous_balance, previous_reading, current_reading)

        WaterBill.objects.create(
            unit=unit,
            property=unit.property,
            tenant=unit.tenant,
            year=year,
            month=month,
            previous_balance=previous_balance,
            previous_reading=previous_reading,
            current_reading=current_reading,
            meter_number=unit.water_meter_number
        )
        return redirect("water-bills")
    return render(request, 'water_bills/new_water_bill.html')


@login_required
def edit_water_bill(request):
    if request.method == "POST":
        water_bill_id = request.POST.get('water_bill_id')
    
        previous_balance = request.POST.get('previous_balance')
        previous_reading = request.POST.get('previous_reading')
        current_reading = request.POST.get('current_reading')

        month_name = request.POST.get('month')
        year_id = request.POST.get('year')

        year = Year.objects.get(id=year_id)
        month = Month.objects.get(name=month_name, year=year)

        water_bill = WaterBill.objects.get(id=water_bill_id)
        water_bill.previous_balance = previous_balance
        water_bill.previous_reading = previous_reading
        water_bill.current_reading = current_reading
        water_bill.month = month
        water_bill.year = year
        water_bill.save()

        water_bill.amount = water_bill.total_amount()
        water_bill.save()

        return redirect("water-bills")
    return render(request, 'water_bills/edit_bill.html')


@login_required
def delete_water_bill(request):
    if request.method == "POST":
        water_bill_id = request.POST.get('water_bill_id')
        WaterBill.objects.get(id=water_bill_id).delete()
        return redirect("water-bills")
    return render(request, 'water_bills/delete_bill.html')
