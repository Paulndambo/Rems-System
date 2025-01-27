from django.db.models import Sum, Count
from django.db.models.functions import ExtractMonth, TruncMonth
from datetime import datetime, timedelta
from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.properties.models import Property, WaterBill, PropertyUnit
from apps.tenants.models import Tenant
#from apps.payments.models import WaterBill, TenantMonthlyBill
from apps.core.models import WaterPrice, Year, Month
from apps.payments.models import RentPayment, RentBill
from apps.core.constants import MONTHS_LIST, UserRoles, MaintenanceStatuses
import json

# Create your views here.
@login_required
def home(request):
    if request.user.role == UserRoles.CARETAKER.value:
        return redirect("caretaker-dashboard")
    
    # Basic stats
    properties_count = Property.objects.count()
    tenants_count = Tenant.objects.filter(is_active=True).count()
    
    # Get total revenue (sum of all paid rent)
    total_revenue = RentBill.objects.all(
    ).aggregate(
        total=Sum('amount_paid')
    )['total'] or 0
    
    # Get monthly revenue data for the last 6 months
    current_year = Year.objects.filter(is_active=True).first()
    
    monthly_data = []
    if current_year:
        monthly_data = RentBill.objects.filter(
            month__year=current_year
        ).values('month').annotate(
            expected_amount=Sum('amount_expected'),
            paid_amount=Sum('amount_paid')
        ).order_by('month__created_at')
    
    # Format data for Chart.js
    labels = []
    expected_amounts = []
    paid_amounts = []
    
    for data in monthly_data:
        month = Month.objects.get(id=data['month'])
        labels.append(month.name)
        expected_amounts.append(float(data['expected_amount'] or 0))
        paid_amounts.append(float(data['paid_amount'] or 0))
    
    # Get occupancy data
    total_units = PropertyUnit.objects.count()
    occupied_units = PropertyUnit.objects.filter(is_occupied=True).count()
    vacant_units = total_units - occupied_units
    
    # Get recent activities
    recent_activities = []
    
    # Recent payments
    recent_payments = RentBill.objects.filter(
        status='paid'
    ).select_related('tenant', 'unit', 'month').order_by('-updated_at')[:3]
    
    for payment in recent_payments:
        recent_activities.append({
            'type': 'payment',
            'title': 'New Payment Received',
            'description': f'{payment.tenant.name} paid rent for {payment.unit.unit_number} ({payment.month.name})',
            'timestamp': payment.updated_at,
            'icon_class': 'fa-check',
            'bg_class': 'success'
        })
    
    # Sort activities by timestamp
    recent_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    
    context = {
        'properties_count': properties_count,
        'tenants_count': tenants_count,
        'total_revenue': f"${total_revenue:,.2f}",
        
        # Chart data
        'chart_data': {
            'labels': json.dumps(labels),
            'expected_amounts': json.dumps(expected_amounts),
            'paid_amounts': json.dumps(paid_amounts),
        },
        
        # Occupancy data
        'occupancy_data': {
            'occupied': occupied_units,
            'vacant': vacant_units,
        },
        
        'recent_activities': recent_activities,
    }
    
    return render(request, 'home.html', context)

@login_required
def caretaker_dashboard(request):
    rent_bills = RentBill.objects.exclude(fully_paid=True).order_by('-created_at')
    water_bills = WaterBill.objects.exclude(status__in=[MaintenanceStatuses.COMPLETED.value, MaintenanceStatuses.PAID.value]).order_by('-created_at')

    total_rent = RentBill.objects.aggregate(total_amount=Sum('amount_expected'))['total_amount']
    total_water = WaterBill.objects.aggregate(total_amount=Sum('amount'))['total_amount']

    total_rent_paid = RentBill.objects.aggregate(total_amount=Sum('amount_paid'))['total_amount']
    total_water_paid = WaterBill.objects.aggregate(total_amount=Sum('amount_paid'))['total_amount']

    total_rent_due = total_rent - total_rent_paid
    total_water_due = total_water - total_water_paid
    
    context = {
        "rent_bills": rent_bills[:5],
        "water_bills": water_bills[:5],
        "bill_months": MONTHS_LIST,
        "years": Year.objects.filter(is_active=True).order_by('-created_at'),
        "properties": Property.objects.filter(is_active=True).order_by('-created_at'),
        "total_rent_due": round(total_rent_due, 0) if total_rent_due is not None else 0,
        "total_water_due": round(total_water_due, 0) if total_water_due is not None else 0,
        "units": PropertyUnit.objects.filter(is_occupied=True).order_by('-created_at')
    }
    return render(request, 'caretaker_dashboard.html', context)

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