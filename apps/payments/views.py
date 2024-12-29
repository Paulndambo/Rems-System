from django.shortcuts import render, redirect

from apps.payments.models import WaterBill
from apps.properties.models import PropertyUnit
from apps.core.constants import MONTHS_LIST, YEARS_LIST
# Create your views here.
def water_bills(request):
    bills = WaterBill.objects.all().order_by('-created_at')
    units = PropertyUnit.objects.filter(is_occupied=True)

    context = {
        "bills": bills,
        "units": units,
        "months": MONTHS_LIST,
        "years": YEARS_LIST
    }
    return render(request, 'water_bills/bills.html', context)


def new_bill(request):
    if request.method == "POST":
        unit = request.POST.get("unit")
        year = request.POST.get("year")
        units = request.POST.get("units")
        month = request.POST.get("month")
    
        WaterBill.objects.create(
            unit_id=unit, 
            month=month, 
            year=year, 
            units=units
        )
        return redirect("water-bills")
    return render(request, 'water_bills/new_water_bill.html')


def edit_bill(request):
    if request.method == "POST":
        bill_id = request.POST.get("bill_id")
        unit = request.POST.get("unit")
        month = request.POST.get("month")
        year = request.POST.get("year")
        units = request.POST.get("units")
    
        WaterBill.objects.filter(id=bill_id).update(
            unit_id=unit, 
            month=month, 
            year=year, 
            units=units
        )
        return redirect("water-bills")
    return render(request, 'water_bills/edit_bill.html')


def delete_bill(request):
    if request.method == "POST":
        bill_id = request.POST.get("bill_id")
        WaterBill.objects.get(id=bill_id).delete()
        return redirect("water-bills")
    return render(request, 'water_bills/delete_bill.html')