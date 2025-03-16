from datetime import datetime
import csv
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Sum
from django.core.paginator import Paginator
import json
from django.db.models.functions import ExtractMonth, ExtractYear
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from apps.payments.models import RentBill, WaterBillPayment, Expense, TenantPayment, RentPayment
from apps.properties.models import WaterBill, Property
from apps.core.models import Month, Year
from apps.tenants.models import Tenant

from apps.core.constants import MONTHS_LIST

# Create your views here.
date_today = datetime.now().date()

@login_required
def monthly_rent_report(request):
    # Get filter parameters
    selected_month = request.GET.get('month')
    selected_year = request.GET.get('year')
    selected_property = request.GET.get('property')
    selected_tenant = request.GET.get('tenant')
    export = request.GET.get('export')
    page = request.GET.get('page', 1)  # Get the page number, default to 1

    selected_year = selected_year if selected_year else Year.objects.get(name=str(date_today.year)).id
    # Base queryset
    rent_bills = RentBill.objects.all()
    
    # Apply filters if selected
    if selected_month:
        rent_bills = rent_bills.filter(month__name=selected_month)
    if selected_year:
        rent_bills = rent_bills.filter(year_id=selected_year)
    if selected_property:
        rent_bills = rent_bills.filter(unit__property_id=selected_property)
    if selected_tenant:
        rent_bills = rent_bills.filter(tenant_id=selected_tenant)
        
    # Order by due date
    rent_bills = rent_bills.order_by('due_date')
    
    # Add pagination
    paginator = Paginator(rent_bills, 10)  # Show 10 rent bills per page
    page_obj = paginator.get_page(page)
    
    # Get all years for the filter dropdowns
    years = Year.objects.all().order_by('-name')
    
    # Get the selected year
    if selected_year:
        year = Year.objects.get(id=selected_year)

    # Before the context definition, add aggregation for graph data
    if selected_year:
        # Get monthly totals for the selected year
        monthly_data = []
        for month in MONTHS_LIST:
            month_bills = rent_bills.filter(month__name=month)
            month_expected = month_bills.aggregate(total_expected=Sum('amount_expected'))['total_expected'] or 0
            month_paid = month_bills.aggregate(total_paid=Sum('amount_paid'))['total_paid'] or 0
            
            monthly_data.append({
                'month': month,
                'expected': float(month_expected),
                'paid': float(month_paid)
            })
    else:
        monthly_data = []

    # Handle CSV export
    if export == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="rent_bills_{selected_month or "all"}_{year.name if year else "all" or "all"}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Tenant', 'Unit', 'Month', 'Year', 'Amount Expected', 'Amount Paid', 'Due Date', 'Status'])

        total_amount_expected = rent_bills.aggregate(total_expected=Sum('amount_expected'))['total_expected'] or 0
        total_amount_paid = rent_bills.aggregate(total_paid=Sum('amount_paid'))['total_paid'] or 0
        total_amount_due = total_amount_expected - total_amount_paid
        
        for rent_bill in rent_bills:
            writer.writerow([
                f"{rent_bill.tenant.user.first_name} {rent_bill.tenant.user.last_name}",
                rent_bill.unit.name,
                rent_bill.month.name,
                rent_bill.year.name,
                rent_bill.amount_expected,
                rent_bill.amount_paid,
                rent_bill.due_date,
                rent_bill.status
            ])
        
        writer.writerow(['', '', '', '', '', '', '', ''])
        writer.writerow(['', '', '', '', "Total Expected", total_amount_expected, '', ''])
        writer.writerow(['', '', '', '', "Total Paid", total_amount_paid, '', ''])
        writer.writerow(['', '', '', '', "Total Due", total_amount_due, '', ''])
        return response

    

    # Regular template response
    tenants = Tenant.objects.all().select_related('user')
    context = {
        'rent_bills': page_obj,
        'months': MONTHS_LIST,
        'years': years,
        'properties': Property.objects.all(),
        'tenants': tenants,
        'selected_month': selected_month if selected_month else None,
        'selected_year': int(selected_year) if selected_year else None,
        'selected_property': int(selected_property) if selected_property else None,
        'selected_tenant': int(selected_tenant) if selected_tenant else None,
        'monthly_data': json.dumps(monthly_data),
        'year': year,
    }
    
    return render(request, 'reports/monthly_rent_report.html', context)
        


@login_required
def water_payments_report(request):
    # Get filter parameters
    year = request.GET.get('year')
    month = request.GET.get('month')
    export = request.GET.get('export')
    tenant = request.GET.get('tenant')
    page = request.GET.get('page', 1)  # Get the page number, default to 1

    # Set default year to current year if not specified
    current_year = str(date_today.year)
    default_year = Year.objects.get(name=current_year).id
    year = year if year else default_year

    water_payments = WaterBillPayment.objects.all()
    chart_data_query = WaterBill.objects.all()

    # Apply filters to both queries
    if month and tenant:
        water_payments = water_payments.filter(water_bill__year_id=year, water_bill__month__name=month, water_bill__tenant_id=tenant)
        chart_data_query = chart_data_query.filter(year_id=year, month__name=month, tenant_id=tenant)
    
    elif month:
        water_payments = water_payments.filter(water_bill__year_id=year, water_bill__month__name=month)
        chart_data_query = chart_data_query.filter(year_id=year, month__name=month)
    
    elif tenant:
        # When only tenant is selected, filter by tenant and current year
        water_payments = water_payments.filter(water_bill__year_id=year, water_bill__tenant_id=tenant)
        chart_data_query = chart_data_query.filter(year_id=year, tenant_id=tenant)
    
    else:
        # Default view - show current year's records
        water_payments = water_payments.filter(water_bill__year_id=year)
        chart_data_query = chart_data_query.filter(year_id=year)

    # Prepare data for charts
    chart_data = chart_data_query.values('month__name', 'year__name').annotate(
        total_units=Sum('units_consumed'),
        total_expected=Sum('amount'),
        total_paid=Sum('waterbillpayment__amount_paid')
    ).order_by('year__name', 'month__name')

    months_labels = []
    units_consumed = []
    expected_amounts = []
    paid_amounts = []

    for data in chart_data:
        month_label = f"{data['month__name']} {data['year__name']}"
        months_labels.append(month_label)
        units_consumed.append(float(data['total_units'] or 0))
        expected_amounts.append(float(data['total_expected'] or 0))
        paid_amounts.append(float(data['total_paid'] or 0))

    # Add pagination
    paginator = Paginator(water_payments, 10)  # Show 10 payments per page
    try:
        water_payments_page = paginator.page(page)
    except:
        water_payments_page = paginator.page(1)

    if export == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="water_payments.csv"'  

        writer = csv.writer(response)
        writer.writerow(['Recorded On', 'Tenant', 'House No.', 'Amount Paid', 'Payment Method', 'Payment Date', 'Month'])

        for water_payment in water_payments_page:
            writer.writerow([
                water_payment.created_at.strftime('%Y-%m-%d'),
                f"{water_payment.tenant.user.first_name} {water_payment.tenant.user.last_name}",
                f"{water_payment.water_bill.unit.name} ({water_payment.water_bill.unit.property.name})",
                water_payment.amount_paid,
                water_payment.payment_method,
                water_payment.payment_date.strftime('%Y-%m-%d'),
                f"{water_payment.month.name} ({water_payment.year.name})"
            ])

        return response
    

    context = {
        'water_payments': water_payments_page,  # Changed to paginated queryset
        'years': Year.objects.all(),
        'months': MONTHS_LIST,
        'tenants': Tenant.objects.all(),
        'selected_year': year,
        'selected_month': month,
        'selected_tenant': tenant,
        'months_labels': json.dumps(months_labels),
        'units_consumed': json.dumps(units_consumed),
        'expected_amounts': json.dumps(expected_amounts),
        'paid_amounts': json.dumps(paid_amounts),
    }
    return render(request, 'reports/water_payments_report.html', context)
