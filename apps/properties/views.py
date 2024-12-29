from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required

from apps.properties.models import Property, PropertyUnit, MaintenanceRequest
from apps.core.constants import UNIT_TYPES, UNIT_STATUSES
# Create your views here.
@login_required
def properties(request):
    properties = Property.objects.all()
    return render(request, 'properties/properties.html', {'properties': properties})


@login_required
def property_detail(request, id):
    property = Property.objects.get(id=id)
    units = PropertyUnit.objects.filter(property=property)


    context = {
        'property': property,
        'units': units,
        "unit_types": UNIT_TYPES,
        "unit_statuses": UNIT_STATUSES
    }
    return render(request, 'properties/property_details.html', context)


@login_required
def new_property(request):
    if request.method == "POST":
        owner = request.user
        name = request.POST.get('name')
        description = request.POST.get('description')
        address = request.POST.get('address')
        city = request.POST.get('city')
        
        country = request.POST.get('country')
        units = request.POST.get('units')
        
        Property.objects.create(
            owner=owner, 
            name=name, 
            description=description, 
            address=address, 
            city=city, 
            country=country, 
            units=units
        )
        return redirect("properties")
    return render(request, 'properties/new_property.html')


@login_required
def edit_property(request):
    if request.method == "POST":
        property_id = request.POST.get('property_id')
        name = request.POST.get('name')
        description = request.POST.get('description')
        address = request.POST.get('address')
        city = request.POST.get('city')
        country = request.POST.get('country')
        units = request.POST.get('units')
       
        
        Property.objects.filter(id=property_id).update(
            name=name, 
            description=description, 
            address=address, 
            city=city, 
            country=country, 
            units=units
        )
        return redirect("properties")
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
    return render(request, 'properties/units/units.html', {'units': units})


@login_required
def property_unit_detail(request, id):
    unit = PropertyUnit.objects.get(id=id)

    context = {
        'unit': unit
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
        
        PropertyUnit.objects.create(
            property=property, 
            name=name, 
            rent=rent, 
            size=size,
            unit_type=unit_type,
            status=status,
            floor=floor
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

        unit=PropertyUnit.objects.get(id=unit_id)
        unit.name=name 
        unit.rent=rent 
        unit.size=size
        unit.unit_type=unit_type
        unit.status=status
        unit.floor=floor
        unit.save()
        
        return redirect("property-detail", id=unit.property.id)
    return render(request, 'properties/units/edit_unit.html')


@login_required
def delete_property_unit(request):
    if request.method == "POST":
        unit_id = request.POST.get('unit_id')
        unit = PropertyUnit.objects.get(id=unit_id)
        unit.delete()
        return redirect("property-detail", id=unit.property.id)
    return render(request, 'properties/units/delete_unit.html')



"""Maintenance Requests"""
@login_required
def maintenance_requests(request):
    maintenance_requests = MaintenanceRequest.objects.all().order_by("-created_at")
    units = PropertyUnit.objects.all().order_by("-created_at")

    context = {
        "maintenance_requests": maintenance_requests,
        "units": units
    }
    return render(request, 'properties/maintenance_requests/maintenance_requests.html', context)


@login_required
def new_maintenance_request(request):
    if request.method == "POST":
        unit_id = request.POST.get('unit')
        unit = PropertyUnit.objects.get(id=unit_id)

        title = request.POST.get('title')
        description = request.POST.get('description')

        MaintenanceRequest.objects.create(
            title=title,
            property=unit.property, 
            unit=unit, 
            description=description
        )
        return redirect("maintenance-requests")
    return render(request, 'properties/maintenance_requests/new_maintenance_request.html')


@login_required
def edit_maintenance_request(request):
    if request.method == "POST":
        maintenance_request_id = request.POST.get('request_id')
        title = request.POST.get('title')
        description = request.POST.get('description')
        status = request.POST.get('status')
        unit = request.POST.get('unit')

        maintenance_request = MaintenanceRequest.objects.get(id=maintenance_request_id)
        maintenance_request.title = title
        maintenance_request.description = description
        maintenance_request.status = status
        maintenance_request.unit = PropertyUnit.objects.get(id=unit)
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