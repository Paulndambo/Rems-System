from datetime import datetime
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.payments.models import WaterBillPayment, Expense, RentPayment, RentBill, TenantPayment
from apps.properties.models import WaterBill, PropertyUnit, Property
from apps.core.models import Month, Year

from apps.core.constants import MaintenanceStatuses, UserRoles, MONTHS_LIST, EXPENSE_TYPES_LIST, PaymentMethods, PaymentStatuses, PAYMENT_METHODS

from django.views.generic import ListView
from django.http import JsonResponse
from django.db.models import Q
from django.db import transaction
from datetime import date
from calendar import month_name


date_today = datetime.now().date()


# Create your views here.

class WaterBillPaymentsView(ListView):
    model = WaterBillPayment
    template_name = "payments/water_bill_payments.html"
    context_object_name = "water_bill_payments"
    paginate_by = 9

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        print(f"You are searching for {search_query}")

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query)
                | Q(water_bill__unit__name__icontains=search_query)
            )

        return queryset.order_by("-created_at")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("search", "")
        context["expense_types"] = EXPENSE_TYPES_LIST
        return context

@login_required
def pay_water_bill(request):
    if request.method == "POST":
        water_bill_id = request.POST.get("water_bill_id")
        amount_paid = Decimal(request.POST.get("amount_paying"))
        payment_method = request.POST.get("payment_method")

        bill = WaterBill.objects.get(id=water_bill_id)

        payment = WaterBillPayment.objects.create(
            tenant=bill.unit.tenant,
            water_bill=bill,
            amount_paid=amount_paid, 
            payment_date=date_today,
            month=bill.month,
            year=bill.year,
            payment_method=payment_method
        )

        bill.amount_paid += payment.amount_paid
        bill.save()

        TenantPayment.objects.create(
            tenant=bill.unit.tenant,
            unit=bill.unit,
            amount_paid=payment.amount_paid,
            payment_date=date_today,
            payment_type="Water Bill",
            water_bill_payment=payment,
            month=bill.month,
            year=bill.year,
            payment_method=payment_method
        )

        if bill.amount_paid == bill.amount:
            bill.status = MaintenanceStatuses.PAID.value
            bill.save()
        elif bill.amount_paid < bill.amount:
            bill.status = MaintenanceStatuses.PARTIALLY_PAID.value
            bill.save()
        else:
            bill.status = MaintenanceStatuses.OVERDUE.value
            bill.save()

        return redirect("water-bills")
    return render(request, "water_bills/pay_water_bill.html")


class ExpenseView(ListView):
    model = Expense
    template_name = "expenses/expenses.html"
    context_object_name = "expenses"
    paginate_by = 9


    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        print(f"You are searching for {search_query}")

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query)
                | Q(title__icontains=search_query)
                | Q(expense_type__icontains=search_query)
            )

        return queryset.order_by("-created_at")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("search", "")
        context["expense_types"] = EXPENSE_TYPES_LIST
        return context

@login_required
def add_expense(request):
    if request.method == "POST":
        title = request.POST.get("title")
        amount = request.POST.get("amount")
        expense_type = request.POST.get("expense_type")
        description = request.POST.get("description")
        spend_on = request.POST.get("spend_on")

        Expense.objects.create(
            title=title, 
            amount=amount, 
            expense_type=expense_type, 
            description=description, 
            spend_on=spend_on
        )
        return redirect("expenses")
    return render(request, "expenses/add_expense.html")


@login_required
def edit_expense(request):

    if request.method == "POST":
        expense_id = request.POST.get("expense_id")

        expense = Expense.objects.get(id=expense_id)
        expense.title = request.POST.get("title")
        expense.amount = request.POST.get("amount")
        expense.expense_type = request.POST.get("expense_type")
        expense.description = request.POST.get("description")
        expense.spend_on = request.POST.get("spend_on")
        expense.save()
        return redirect("expenses")
    return render(request, "expenses/edit_expense.html", { "expense_types": EXPENSE_TYPES_LIST })

@login_required
def delete_expense(request):
    if request.method == "POST":
        expense_id = request.POST.get("expense_id")
        expense = Expense.objects.get(id=expense_id)
        expense.delete()
        return redirect("expenses")
    return render(request, "expenses/delete_expense.html")



class MonthlyRentBillsView(ListView):
    model = Month
    template_name = "rent_bills/months.html"
    context_object_name = "months"
    paginate_by = 9


    def get_queryset(self):
        queryset = super().get_queryset()

        bills = RentBill.objects.values_list("month", flat=True)
        months = Month.objects.filter(id__in=bills).values_list("id", flat=True)
        print(months)

        search_query = self.request.GET.get("search", "")

        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query)
                | Q(year__year__icontains=search_query)
            )

        return queryset.filter(id__in=months).order_by("-created_at")
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["payment_methods"] = PAYMENT_METHODS
        context["properties"] = Property.objects.filter(is_active=True)
        context["bill_months"] = MONTHS_LIST
        context["years"] = Year.objects.filter(is_active=True)
        return context



class RentBillsView(ListView):
    model = RentBill
    template_name = "rent_bills/rent_bills.html"
    context_object_name = "rent_bills"
    paginate_by = 9

    def get_queryset(self):
        month_id = self.kwargs.get("month_id")
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        if search_query:
            queryset = queryset.filter(
                Q(tenant__user__first_name__icontains=search_query)
                | Q(unit__name__icontains=search_query)
            )

        return queryset.filter(month_id=month_id).order_by("-created_at")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("search", "")
        context["properties"] = Property.objects.filter(is_active=True)
        context["months"] = Month.objects.filter(is_active=True)
        context["years"] = Year.objects.filter(is_active=True)
        context["payment_methods"] = PAYMENT_METHODS
        return context
    


class CaretakerRentBillsView(ListView):
    model = RentBill
    template_name = "rent_bills/caretaker_rent_bills.html"
    context_object_name = "rent_bills"
    paginate_by = 9

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        if search_query:
            queryset = queryset.filter(
                Q(tenant__user__first_name__icontains=search_query)
                | Q(unit__name__icontains=search_query)
            )

        # Order by fully_paid (False first) and then by created_at
        return queryset.order_by('fully_paid', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("search", "")
        context["payment_methods"] = PAYMENT_METHODS
        return context


class RentReceiptsView(ListView):
    model = RentBill
    template_name = "rent_bills/rent_receipts.html"
    context_object_name = "rent_receipts"
    

    def get_queryset(self):
        month_id = self.kwargs.get("month_id")
        queryset = super().get_queryset()

        return queryset.filter(month_id=month_id).order_by("-created_at")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("search", "")
        return context


def single_receipt(request, rent_receipt_id):
    rent_receipt = RentBill.objects.get(id=rent_receipt_id)
    return render(request, "rent_bills/single_receipt.html", { "rent_receipt": rent_receipt })

@login_required
@transaction.atomic
def generate_rent_bill(request):
    user = request.user
    if request.method == "POST":
        month = request.POST.get("month")
        year = request.POST.get("year")
        property_id = request.POST.get("property_id")
        due_date = request.POST.get("due_date")

        
        year = Year.objects.get(id=year)
        month = Month.objects.get(name=month, year=year)

        print(f"Month: {month}, Year: {year}, Property: {property_id}, Due Date: {due_date}")

        existing_bills = RentBill.objects.filter(month=month, year=year, unit__property_id=property_id)
        if existing_bills.exists():
            messages.error(request, "Rent bills for this month already exist.")

            if user.role == UserRoles.CARETAKER.value:
                return redirect("caretaker-rent-bills")
            else:
                return redirect("monthly-rent-bills")

        units = PropertyUnit.objects.filter(is_occupied=True).filter(property_id=property_id)

        for unit in units:
            print(f"Unit: {unit.name}, Rent Amount: {unit.rent}")

        units_list = []
        for unit in units:
            units_list.append(RentBill(
                    unit=unit,
                    tenant=unit.tenant,
                    amount_expected=unit.rent,
                    due_date=due_date,
                    month=month,
                    year=year,
                )
            )

        RentBill.objects.bulk_create(units_list)

        if user.role == UserRoles.CARETAKER.value:
            return redirect("caretaker-rent-bills")
        else:
            return redirect("monthly-rent-bills")

    return render(request, "rent_bills/generate_rent_bill.html")


class RentPaymentsView(ListView):
    model = RentPayment
    template_name = "rent_payments/rent_payments.html"
    context_object_name = "rent_payments"
    paginate_by = 9

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        if search_query:
            queryset = queryset.filter(
                Q(rent_bill__tenant__user__first_name__icontains=search_query)
                | Q(rent_bill__unit__name__icontains=search_query)
            )

        return queryset.order_by("-created_at")
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("search", "")
        context["payment_methods"] = PaymentMethods.choices()
        return context

@login_required
def pay_rent(request):
    user = request.user
    if request.method == "POST":
        rent_bill_id = request.POST.get("rent_bill_id")
        amount_paid = Decimal(request.POST.get("amount_paid"))
        payment_method = request.POST.get("payment_method")
        payment_date = request.POST.get("payment_date")

        rent_bill = RentBill.objects.get(id=rent_bill_id)
        rent_bill.amount_paid += amount_paid
        rent_bill.save()

        rent_payment = RentPayment.objects.create(
            rent_bill_id=rent_bill_id,
            amount_paid=amount_paid,
            payment_method=payment_method,
            payment_date=payment_date
        )

        TenantPayment.objects.create(
            tenant=rent_bill.tenant,
            unit=rent_bill.unit,
            amount_paid=amount_paid,
            payment_date=payment_date,
            month=rent_bill.month,
            year=rent_bill.year,
            rent_payment=rent_payment,
            payment_type="Rent Bill",
            payment_method=payment_method
        )

        if rent_bill.amount_paid == rent_bill.amount_expected:
            rent_bill.status = PaymentStatuses.PAID.value
            rent_bill.fully_paid = True
            rent_bill.save()
        elif rent_bill.amount_paid < rent_bill.amount_expected:
            rent_bill.status = PaymentStatuses.PARTIALLY_PAID.value
            rent_bill.save()
        else:
            rent_bill.status = PaymentStatuses.PENDING.value
            rent_bill.save()

        if user.role == UserRoles.CARETAKER.value:
            return redirect("caretaker-rent-bills")
        else:
            return redirect("rent-payments")
    return render(request, "rent_payments/pay_rent.html")


def generate_rent_payment(request):
    if request.method == "POST":
        pass
    return render(request, "rent_payments/generate_rent_payment.html")


def rent_payments_overview(request):
    units = PropertyUnit.objects.order_by("name")
    unit_numbers = [unit.name for unit in units]

    # Fetch rent data grouped by month, year, and unit
    rent_data = {}
    bills = RentBill.objects.select_related("unit", "month", "year")
    for bill in bills:
        month_key = f"{bill.year.name}-{bill.month.name}"  # e.g., "2025-January"
        if month_key not in rent_data:
            rent_data[month_key] = {}
        rent_data[month_key][bill.unit.name] = bill.fully_paid  # Store fully_paid status

    # Generate rows for the table
    rows = []
    for month_key in sorted(rent_data.keys()):  # Sort by year-month
        month_display = month_key.split("-")[1]  # Extract month name
        year_display = month_key.split("-")[0]  # Extract year
        row = [f"{month_display} {year_display}"]  # Month and year as the first column
        for unit in unit_numbers:
            row.append(rent_data[month_key].get(unit, None))  # Get fully_paid or None
        rows.append(row)

    context = {
        "unit_numbers": unit_numbers,
        "rows": rows,
    }
    return render(request, "rent_payments/overview.html", context)