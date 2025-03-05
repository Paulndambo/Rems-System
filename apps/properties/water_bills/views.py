from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from datetime import datetime
from decimal import Decimal
from django.views.generic import ListView
from django.http import JsonResponse
from django.db.models import Q
from django.db import transaction

from apps.properties.models import Property, PropertyUnit, MaintenanceRequest, WaterBill
from apps.core.models import Month, Year
from apps.tenants.models import Tenant
from apps.payments.models import TenantPayment, RentPayment, RentBill, UnitMonthBill, GarbageBill
from apps.users.models import User

from apps.core.constants import UNIT_TYPES, UNIT_STATUSES, GENDER_LIST, MONTHS_LIST, PAYMENT_METHODS
# Create your views here.

@login_required
@transaction.atomic
def new_water_bill(request):
    if request.method == "POST":
        unit_id = request.POST.get('unit')
        
        year_id = request.POST.get('year')
        month_name = request.POST.get('month')
        previous_balance = request.POST.get('previous_balance')
        #current_reading = request.POST.get('current_reading')
        units_consumed = Decimal(request.POST.get('units_consumed'))

        

        unit = PropertyUnit.objects.get(id=unit_id)
        year = Year.objects.get(id=year_id)
        month = Month.objects.get(name=month_name, year=year)

        unit_bill = UnitMonthBill.objects.filter(unit=unit, month=month, year=year).first()

        if not unit_bill:
            unit_bill = UnitMonthBill.objects.create(
                unit=unit,
                tenant=unit.tenant,
                month=month,
                year=year
            )

    
        unit_bill.water_amount = (Decimal(unit.water_price) * Decimal(units_consumed)) + Decimal(previous_balance)
        unit_bill.update_amount_expected()
        unit_bill.save()

        water_bill = WaterBill.objects.create(
            unit_bill=unit_bill,
            unit=unit,
            property=unit.property,
            tenant=unit.tenant,
            year=year,
            month=month,
            previous_balance=0,
            current_reading=0,
            meter_number=unit.water_meter_number,
            units_consumed=units_consumed,
            amount=unit_bill.water_amount
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
