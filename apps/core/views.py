from django.db import models
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.properties.models import Property
from apps.tenants.models import Tenant
#from apps.payments.models import WaterBill, TenantMonthlyBill
from apps.core.models import WaterPrice, Year, Month
from apps.core.constants import MONTHS_LIST
# Create your views here.
@login_required
def home(request):
    tenants_count = Tenant.objects.count()
    properties_count = Property.objects.count()
    #total_revenue = TenantMonthlyBill.objects.aggregate(total_amount=models.Sum('amount_paid'))['total_amount']

    context = {
        'tenants_count': tenants_count,
        'properties_count': properties_count, 
        #'total_revenue': total_revenue if total_revenue is not None else 0
    }
    return render(request, 'home.html', context)



@login_required
def years(request):
    years = Year.objects.all().order_by('-created_at')
    context = {
        "years": years
    }
    return render(request, 'settings/years.html', context)


@login_required
def new_year(request):
    if request.method == 'POST':
        name = request.POST.get('name')

        year = Year.objects.create(name=name)

        for month in MONTHS_LIST:
            Month.objects.create(name=month, year=year)

        return redirect("years")
    return render(request, 'settings/new_year.html')


@login_required
def deactivate_year(request, id):
    year = Year.objects.get(id=id)
    year.is_active = False
    year.months.update(is_active=False)
    year.save()
    return redirect("years")


@login_required
def activate_year(request, id):
    year = Year.objects.get(id=id)
    year.is_active = True
    year.months.update(is_active=True)
    year.save()
    return redirect("years")


@login_required
def months(request):
    months = Month.objects.all().order_by('-created_at')
    context = {
        "months": months
    }
    return render(request, 'settings/months.html', context)


@login_required
def water_prices(request):
    water_prices = WaterPrice.objects.all().order_by('-created_at')
    context = {
        "water_prices": water_prices
    }
    return render(request, 'settings/water_prices.html', context)


@login_required
def edit_water_price(request):
    if request.method == 'POST':
        water_price_id = request.POST.get('water_price_id')
        unit_price = request.POST.get('unit_price')

        WaterPrice.objects.filter(id=water_price_id).update(unit_price=unit_price)
        return redirect("water-prices")
    return render(request, 'settings/edit_water_price.html')