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
from django.http import JsonResponse
from django.views.decorators.http import require_GET

# Create your views here.
@login_required
def home(request):
    if request.user.role == UserRoles.CARETAKER.value:
        return redirect("caretaker-dashboard")
    

    year = datetime.now().date().year
    print(f"Current Year: {year}")
    month_ids_list = list(RentBill.objects.filter(month__year__name=str(year)).values_list('month__id', flat=True).distinct())

    # Basic stats
    properties_count = Property.objects.count()
    tenants_count = Tenant.objects.all().count()
    
    # Get total revenue (sum of all paid rent)
    total_revenue = RentBill.objects.filter(month__in=month_ids_list).aggregate(
        total=Sum('amount_paid')
    )['total'] or 0
    
    # Get monthly revenue data for the last 6 months
    
    
    monthly_data = []
    if year:
        monthly_data = RentBill.objects.filter(
            month__in=month_ids_list
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
    recent_payments = RentBill.objects.filter(month__in=month_ids_list, status='paid').select_related('tenant', 'unit', 'month').order_by('-updated_at')[:3]
    
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
    
    # Add available years for the filter
    # You might want to get this from your database
    current_year = datetime.now().year
    available_years = list(range(current_year - 3, current_year + 1))
    
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
        'available_years': available_years,
        'current_year': current_year,
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

@require_GET
def chart_data_api(request):
    """API endpoint to get chart data for a specific year"""
    year = request.GET.get('year', datetime.now().year)
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
    
    return JsonResponse({
        'revenue': revenue_data,
        'occupancy': occupancy_data,
        'total_revenue': f"Kes {total_revenue:,.2f}"  # Format as currency
    })

def get_revenue_data_for_year(year):
    # Get monthly data for the specified year

    # Get all months for the specified year
    months_list = list(RentBill.objects.filter(month__year__name=str(year)).values_list('month__id', flat=True).distinct())
    
    
    monthly_data = RentBill.objects.filter(month__in=months_list).values('month').annotate(
        expected_amount=Sum('amount_expected'),
        paid_amount=Sum('amount_paid')
    ).order_by('month__created_at')
    
    labels = []
    expected_amounts = []
    paid_amounts = []
    
    # Only process months that have RentBill records
    # This is already happening since we're iterating over the query results
    for data in monthly_data:
        month = Month.objects.get(id=data['month'])
        labels.append(month.name)
        expected_amounts.append(float(data['expected_amount'] or 0))
        paid_amounts.append(float(data['paid_amount'] or 0))
    
    return {
        'labels': labels,
        'expected_amounts': expected_amounts,
        'paid_amounts': paid_amounts
    }

def get_occupancy_data_for_year(year):
    # Implement logic to get occupancy data for the specified year
    # Example:
    occupied_units = PropertyUnit.objects.filter(is_occupied=True).count()
    total_units = PropertyUnit.objects.all().count()
    vacant_units = total_units - occupied_units
    return {
        'occupied': occupied_units,  # Number of occupied units for the selected year
        'vacant': vacant_units      # Number of vacant units for the selected year
    }

def calculate_total_revenue_for_year(year):
    # Your logic to calculate total revenue for the given year
    # For example:
    
    total = RentBill.objects.filter(
        year__name=str(year)
    ).aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    
    return total