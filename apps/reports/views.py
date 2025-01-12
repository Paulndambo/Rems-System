import csv
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Sum

from apps.payments.models import RentBill, WaterBillPayment, Expense, TenantPayment
from apps.properties.models import WaterBill
from apps.core.models import Month, Year
from apps.tenants.models import Tenant

from apps.core.constants import MONTHS_LIST

# Create your views here.
def monthly_rent_report(request):
    # Get filter parameters
    selected_month = request.GET.get('month')
    selected_year = request.GET.get('year')
    export = request.GET.get('export')
    
    # Base queryset
    rent_bills = RentBill.objects.all()
    
    # Apply filters if selected
    if selected_month:
        rent_bills = rent_bills.filter(month__name=selected_month)
    if selected_year:
        rent_bills = rent_bills.filter(year_id=selected_year)
        
    # Order by due date
    rent_bills = rent_bills.order_by('due_date')
    
    # Get all years for the filter dropdowns
    years = Year.objects.all().order_by('-name')

    year = None
    if selected_year:
        year = Year.objects.get(id=selected_year)

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
    context = {
        'rent_bills': rent_bills,
        'months': MONTHS_LIST,
        'years': years,
        'selected_month': selected_month if selected_month else None,
        'selected_year': int(selected_year) if selected_year else None,
    }
    
    return render(request, 'reports/monthly_rent_report.html', context)
        


def expenses_report(request):
    # Get filter parameters
    expense_type = request.GET.get('expense_type')
    export = request.GET.get('export')

    # Base queryset
    expenses = Expense.objects.all()

    # Apply filters if selected
    if expense_type:
        expenses = expenses.filter(expense_type=expense_type)

    # Order by date
    expenses = expenses.order_by('spend_on')

    # Handle CSV export
    if export == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="expenses.csv"'  

        writer = csv.writer(response)
        writer.writerow(['Recorded On', 'Name', 'Description', 'Amount', 'Category', 'Spend On'])

        for expense in expenses:
            writer.writerow([expense.created_at.strftime('%Y-%m-%d'), expense.title, expense.description, expense.amount, expense.expense_type, expense.spend_on.strftime('%Y-%m-%d')])

        return response
    
    # Regular template response
    context = {
        'expenses': expenses,
        'expense_types': ["Electricity", "Water", "Gas", "Internet", "Maintenance", "Other"],
    }

    return render(request, 'reports/expenses_report.html', context)



def water_bills_report(request):
    # Get filter parameters
    year = request.GET.get('year')
    month = request.GET.get('month')
    export = request.GET.get('export')
    tenant = request.GET.get('tenant')

    water_bills = WaterBill.objects.all()

    if year and month and tenant:
        water_bills = water_bills.filter(year_id=year, month__name=month, tenant_id=tenant)
    
    elif year and month:
        water_bills = water_bills.filter(year_id=year, month__name=month)
    
    elif month and tenant:
        water_bills = water_bills.filter(month__name=month, tenant_id=tenant)

    elif tenant and year:
        water_bills = water_bills.filter(tenant_id=tenant, year_id=year)

    elif tenant:
        water_bills = water_bills.filter(tenant_id=tenant)

    elif year:
        water_bills = water_bills.filter(year_id=year)

    elif month:
        water_bills = water_bills.filter(month__name=month)

    if export == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="water_bills.csv"'  

        writer = csv.writer(response)
        writer.writerow(['Recorded On', 'Tenant', 'House No.', 'Month', 'Previous Reading', 'Month Reading', 'Amount Expected', 'Amount Paid', 'Status'])

        for water_bill in water_bills:
            writer.writerow([
                water_bill.created_at.strftime('%Y-%m-%d'),
                f"{water_bill.tenant.user.first_name} {water_bill.tenant.user.last_name}",
                f"{water_bill.unit.name} ({water_bill.unit.property.name})",
                f"{water_bill.month.name} ({water_bill.year.name})",
                water_bill.previous_reading,
                water_bill.current_reading,
                water_bill.amount,
                water_bill.amount_paid,
                water_bill.status
            ])

        return response
    

    context = {
        'water_bills': water_bills,
        'years': Year.objects.all(),
        'months': MONTHS_LIST,
        'tenants': Tenant.objects.all(),
        'selected_year': year,
        'selected_month': month,
        'selected_tenant': tenant,
    }
    return render(request, 'reports/water_bills_report.html', context)


def water_bills_payments_report(request):
    # Get filter parameters
    year = request.GET.get('year')
    month = request.GET.get('month')
    export = request.GET.get('export')
    tenant = request.GET.get('tenant')

    water_payments = WaterBillPayment.objects.all()

    if year and month and tenant:
        water_payments = water_payments.filter(year_id=year, month__name=month, tenant_id=tenant)
    
    elif year and month:
        water_payments = water_payments.filter(year_id=year, month__name=month)
    
    elif month and tenant:
        water_payments = water_payments.filter(month__name=month, tenant_id=tenant)

    elif tenant:
        water_payments = water_payments.filter(tenant_id=tenant)

    elif year:
        water_payments = water_payments.filter(year_id=year)

    elif month:
        water_payments = water_payments.filter(month__name=month)


    if export == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="water_payments.csv"'  

        writer = csv.writer(response)
        writer.writerow(['Recorded On', 'Tenant', 'House No.', 'Amount Paid', 'Payment Method', 'Payment Date', 'Month'])

        for water_payment in water_payments:
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
        'water_payments': water_payments,
        'years': Year.objects.all(),
        'months': MONTHS_LIST,
        'tenants': Tenant.objects.all(),
        'selected_year': year,
        'selected_month': month,
        'selected_tenant': tenant,
    }
    return render(request, 'reports/water_payments_report.html', context)


def tenant_payments_report(request):
    # Get filter values from request
    year = request.GET.get('year')
    month = request.GET.get('month')
    tenant = request.GET.get('tenant')
    export = request.GET.get('export')

    # Filter payments based on selected filters
    tenant_payments = TenantPayment.objects.all()

    if year and month and tenant:
        tenant_payments = tenant_payments.filter(year_id=year, month__name=month, tenant_id=tenant)
    
    elif year and month:
        tenant_payments = tenant_payments.filter(year_id=year, month__name=month)
    
    elif year and tenant:
        tenant_payments = tenant_payments.filter(year_id=year, tenant_id=tenant)
    
    elif month and tenant:
        tenant_payments = tenant_payments.filter(month__name=month, tenant_id=tenant)

    elif tenant:
        tenant_payments = tenant_payments.filter(tenant_id=tenant)

    elif year:
        tenant_payments = tenant_payments.filter(year_id=year)

    elif month:
        tenant_payments = tenant_payments.filter(month__name=month)

    # Get distinct years, months, and tenants for filters

    if export == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="tenant_payments.csv"'  

        writer = csv.writer(response)
        writer.writerow(['Recorded On', 'Tenant', 'House No.', 'Amount Paid', 'Payment Method', 'Payment Date', 'Month', 'Year', 'Payment Type'])

        for payment in tenant_payments:
            writer.writerow([ 
                payment.created_at.strftime('%Y-%m-%d'),
                f"{payment.tenant.user.first_name} {payment.tenant.user.last_name}", 
                payment.unit.name, 
                payment.amount_paid, 
                payment.payment_method, 
                payment.payment_date.strftime('%Y-%m-%d'), 
                payment.month.name, 
                payment.year.name, 
                payment.payment_type
            ])

        return response
    

    context = {
        'tenant_payments': tenant_payments,
        'years': Year.objects.all(),
        'months': MONTHS_LIST,
        'tenants': Tenant.objects.all(),
        'selected_year': year,
        'selected_month': month,
        'selected_tenant': tenant,
    }
    return render(request, 'reports/tenant_payments_report.html', context)

