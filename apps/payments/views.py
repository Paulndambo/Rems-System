from calendar import month_name
from datetime import date, datetime
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest, JsonResponse
from django.shortcuts import render, redirect
from django.views.generic import ListView

from apps.core.constants import (
    MaintenanceStatuses,
    UserRoles,
    MONTHS_LIST,
    EXPENSE_TYPES_LIST,
    PaymentMethods,
    PaymentStatuses,
    PAYMENT_METHODS,
)
from apps.core.models import Month, Year
from apps.payments.models import (
    WaterBillPayment,
    Expense,
    RentPayment,
    RentBill,
    TenantPayment,
    UnitMonthBill,
    SecurityDeposit,
    SecurityDepositPayment,
    TemporaryMonthBill
)
from apps.properties.models import WaterBill, PropertyUnit, Property
from apps.payments.models import GarbageBill
from apps.properties.water_bills.billing_mixin import TenantBillingMixin              

# Move global variable to top
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
    if request.method != "POST":
        return render(request, "water_bills/pay_water_bill.html")

    water_bill_id = request.POST.get("water_bill_id")
    amount_paid = Decimal(request.POST.get("amount_paying"))
    payment_method = request.POST.get("payment_method")

    bill = WaterBill.objects.get(id=water_bill_id)

    # Create water bill payment
    payment = WaterBillPayment.objects.create(
        tenant=bill.unit.tenant,
        water_bill=bill,
        amount_paid=amount_paid,
        payment_date=date_today,
        month=bill.month,
        year=bill.year,
        payment_method=payment_method,
    )

    # Update bill amounts and status
    bill.amount_paid += payment.amount_paid
    if bill.amount_paid == bill.amount:
        bill.status = MaintenanceStatuses.PAID.value
    elif bill.amount_paid < bill.amount:
        bill.status = MaintenanceStatuses.PARTIALLY_PAID.value
    else:
        bill.status = MaintenanceStatuses.OVERDUE.value
    bill.save()

    # Create tenant payment record
    TenantPayment.objects.create(
        tenant=bill.unit.tenant,
        unit=bill.unit,
        amount_paid=payment.amount_paid,
        payment_date=date_today,
        payment_type="Water Bill",
        water_bill_payment=payment,
        month=bill.month,
        year=bill.year,
        payment_method=payment_method,
    )

    # Update unit bill amounts and status
    bill.unit_bill.amount_paid += payment.amount_paid
    if bill.unit_bill.amount_paid == bill.unit_bill.amount_expected:
        bill.unit_bill.status = PaymentStatuses.PAID.value
    elif bill.unit_bill.amount_paid < bill.unit_bill.amount_expected:
        bill.unit_bill.status = PaymentStatuses.PARTIALLY_PAID.value
    else:
        bill.unit_bill.status = PaymentStatuses.PENDING.value
    bill.unit_bill.save()

    return redirect("water-bills")


class ExpenseView(ListView):
    model = Expense
    template_name = "expenses/expenses.html"
    context_object_name = "expenses"
    paginate_by = 9

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query)
                | Q(title__icontains=search_query)
                | Q(expense_type__icontains=search_query)
                | Q(unit__name__icontains=search_query)
                | Q(property__name__icontains=search_query)
            )

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("search", "")
        context["expense_types"] = EXPENSE_TYPES_LIST
        context["properties"] = Property.objects.filter(is_active=True)
        context["units"] = PropertyUnit.objects.all()
        return context


@login_required
def add_expense(request):
    if request.method != "POST":
        context = {
            "expense_types": EXPENSE_TYPES_LIST,
            "properties": Property.objects.filter(is_active=True),
            "units": PropertyUnit.objects.all(),
        }
        return render(request, "expenses/new_expense.html", context)

    Expense.objects.create(
        title=request.POST.get("title"),
        amount=request.POST.get("amount"),
        expense_type=request.POST.get("expense_type"),
        description=request.POST.get("description"),
        spend_on=request.POST.get("spend_on"),
        property_id=request.POST.get("property"),
        unit_id=request.POST.get("unit"),
    )
    return redirect("expenses")


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

        property_id = request.POST.get("property")
        unit_id = request.POST.get("unit")

        expense.property_id = property_id
        expense.unit_id = unit_id
        expense.save()
        return redirect("expenses")
    
    expense_id = request.GET.get('id')
    expense = Expense.objects.filter(id=expense_id).first() if expense_id else None
    
    context = {
        "expense": expense,
        "expense_types": EXPENSE_TYPES_LIST,
        "properties": Property.objects.filter(is_active=True),
        "units": PropertyUnit.objects.all(),
    }
    return render(request, "expenses/edit_expense.html", context)


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

        search_query = self.request.GET.get("search", "")

        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) | Q(year__year__icontains=search_query)
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
        return queryset.order_by("fully_paid", "-created_at")

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
    return render(
        request, "rent_bills/single_receipt.html", {"rent_receipt": rent_receipt}
    )


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

        existing_bills = RentBill.objects.filter(
            month=month, year=year, unit__property_id=property_id
        )
        if existing_bills.exists():

            if user.role == UserRoles.CARETAKER.value:
                return redirect("caretaker-rent-bills")
            else:
                return redirect("monthly-rent-bills")

        units = PropertyUnit.objects.filter(is_occupied=True).filter(
            property_id=property_id
        )

        units_list = []
        for unit in units:
            unit_bill = UnitMonthBill.objects.filter(
                unit=unit, month=month, year=year
            ).first()

            if not unit_bill:
                unit_bill = UnitMonthBill.objects.create(
                    unit=unit, tenant=unit.tenant, month=month, year=year
                )

            unit_bill.rent_amount = unit.rent
            unit_bill.garbage_amount = unit.property.garbage_charge
            unit_bill.update_amount_expected()
            unit_bill.save()

            units_list.append(
                RentBill(
                    unit=unit,
                    unit_bill=unit_bill,
                    tenant=unit.tenant,
                    amount_expected=unit.rent,
                    due_date=due_date,
                    month=month,
                    year=year,
                )
            )
            garbage_bill = GarbageBill.objects.filter(
                unit=unit, unit_bill=unit_bill
            ).first()
            if not garbage_bill:
                garbage_bill = GarbageBill.objects.create(
                    unit_bill=unit_bill,
                    unit=unit,
                    tenant=unit.tenant,
                    amount_expected=unit.property.garbage_charge,
                    due_date=due_date,
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
            payment_date=payment_date,
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
            payment_method=payment_method,
        )

        rent_bill.unit_bill.amount_paid += amount_paid
        rent_bill.unit_bill.save()

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

        if rent_bill.unit_bill.amount_paid == rent_bill.unit_bill.amount_expected:
            rent_bill.unit_bill.status = PaymentStatuses.PAID.value
            rent_bill.unit_bill.save()
        elif rent_bill.unit_bill.amount_paid < rent_bill.unit_bill.amount_expected:
            rent_bill.unit_bill.status = PaymentStatuses.PARTIALLY_PAID.value
            rent_bill.unit_bill.save()
        else:
            rent_bill.unit_bill.status = PaymentStatuses.PENDING.value
            rent_bill.unit_bill.save()

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
        rent_data[month_key][
            bill.unit.name
        ] = bill.fully_paid  # Store fully_paid status

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


class SecurityDepositsView(ListView):
    model = SecurityDeposit
    template_name = "security_deposits/security_deposits.html"
    context_object_name = "security_deposits"
    paginate_by = 9

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query)
                | Q(tenant__user__first_name__icontains=search_query)
                | Q(unit__name__icontains=search_query)
            )

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("search", "")
        context["payment_methods"] = PaymentMethods.choices()
        return context


@login_required
def pay_security_deposit(request: HttpRequest):
    if request.method == "POST":
        security_deposit_id = request.POST.get("security_deposit_id")
        amount_paid = Decimal(request.POST.get("amount_paid"))
        payment_method = request.POST.get("payment_method")
        payment_date = request.POST.get("payment_date")
        reference_number = request.POST.get("reference_number")

        security_deposit = SecurityDeposit.objects.get(id=security_deposit_id)
        security_deposit.amount_paid += amount_paid
        security_deposit.save()

        if security_deposit.amount_paid == security_deposit.amount_expected:
            security_deposit.status = PaymentStatuses.PAID.value
            security_deposit.fully_paid = True
            security_deposit.save()
        elif security_deposit.amount_paid < security_deposit.amount_expected:
            security_deposit.status = PaymentStatuses.PARTIALLY_PAID.value
            security_deposit.save()
        else:
            security_deposit.status = PaymentStatuses.PENDING.value
            security_deposit.save()

        security_deposit_payment = SecurityDepositPayment.objects.create(
            security_deposit=security_deposit,
            amount_paid=amount_paid,
            payment_method=payment_method,
            payment_date=payment_date,
            reference_number=reference_number,
        )

        TenantPayment.objects.create(
            tenant=security_deposit.tenant,
            unit=security_deposit.unit,
            amount_paid=amount_paid,
            payment_date=payment_date,
            security_deposit_payment=security_deposit_payment,
            payment_type="Security Deposit",
            payment_method=payment_method,
        )

        return redirect("security-deposits")
    return render(request, "payments/pay_security_deposit.html")


def temporary_month_bills_view(request: HttpRequest):
    bills = TemporaryMonthBill.objects.filter(status__in=["Pending", "Captured"]).select_related("unit", "month", "year").order_by("-created_at")

    context = {
        "bills": bills,
    }
    return render(request, "water_bills/temporary_month_bills.html", context)


@transaction.atomic
def generate_temporary_month_bill(request: HttpRequest):
    if request.method == "POST":
        month = request.POST.get("month")
        year = str(date_today.year)

        month_obj = Month.objects.get(name=month, year__name=year)

        for unit in PropertyUnit.objects.filter(is_occupied=True):
            monthly_bill_exists = UnitMonthBill.objects.filter(
                unit=unit, month=month_obj, year__name=year
            ).exists()

            temporary_month_bill_exists = TemporaryMonthBill.objects.filter(
                unit=unit, month=month_obj, year__name=year
            ).exists()

            if monthly_bill_exists or temporary_month_bill_exists:
                continue
            else:
                last_water_bill = WaterBill.objects.filter(unit=unit).order_by("-created_at").first()
                previous_reading = last_water_bill.current_reading if last_water_bill else 0

                TemporaryMonthBill.objects.create(
                    unit=unit,
                    month=month_obj,
                    year=month_obj.year,
                    rent_amount=unit.rent,
                    garbage_amount=unit.property.garbage_charge,
                    previous_reading=previous_reading,
                )

        return redirect("temporary-month-bills")
    return render(request, "water_bills/generate_temporary_month_bill.html", {"months": MONTHS_LIST})



def capture_current_meter_readings(request: HttpRequest):
    if request.method == "POST":
        bill_id = request.POST.get("bill_id")
        current_reading = request.POST.get("current_reading")

        bill = TemporaryMonthBill.objects.get(id=bill_id)
        bill.current_reading = current_reading
        bill.status = "Captured"
        bill.save()

        return redirect("temporary-month-bills")
    return render(request, "water_bills/capture_current_meter_reading.html")


@transaction.atomic
def confirm_current_meter_readings(request: HttpRequest):
    if request.method == "POST":
        bill_id = request.POST.get("bill_id")

        bill = TemporaryMonthBill.objects.get(id=bill_id)
        bill.status = "Confirmed"
        bill.save()

        try:
            biller = TenantBillingMixin(
                year=bill.year,
                month=bill.month,
                previous_reading=bill.previous_reading,
                current_reading=bill.current_reading,
                unit=bill.unit
            )

            biller.generate_bill()

            messages.success(request, f"Bill successfully generated for {bill.unit.name} - {bill.month.name} {bill.year.name}")
        except Exception as e:
            messages.error(request, f"Error confirming meter reading: {str(e)}")
            raise e

        return redirect("temporary-month-bills")
    return render(request, "water_bills/confirm_current_meter_reading.html")



def edit_current_meter_reading(request: HttpRequest):
    if request.method == "POST":
        bill_id = request.POST.get("bill_id")
        current_reading = request.POST.get("current_reading")

        bill = TemporaryMonthBill.objects.get(id=bill_id)
        bill.current_reading = current_reading
        bill.save()

        return redirect("temporary-month-bills")
    return render(request, "water_bills/edit_current_meter_reading.html")



def pending_bills_view(request: HttpRequest):
    bills = UnitMonthBill.objects.filter(status__in=["Pending", "Partially Paid"]).select_related("unit", "month", "year").order_by("-created_at")

    context = {
        "bills": bills,
    }
    return render(request, "water_bills/pending_bills.html", context)

def collect_pending_bill(request: HttpRequest):
    if request.method == "POST":
        bill_id = request.POST.get("bill_id")
        amount_paid = Decimal(request.POST.get("amount_paid"))
        payment_method = request.POST.get("payment_method")
        payment_date = request.POST.get("payment_date")

        bill = UnitMonthBill.objects.get(id=bill_id)
        bill.amount_paid += amount_paid
        bill.save()

        TenantPayment.objects.create(
            tenant=bill.tenant,
            unit=bill.unit,
            amount_paid=amount_paid,
            payment_date=payment_date,
            month=bill.month,
            year=bill.year,
            payment_type="Unit Month Bill",
            payment_method=payment_method,
        )

        if bill.amount_paid == bill.amount_expected:
            bill.status = PaymentStatuses.PAID.value
            bill.save()
        elif bill.amount_paid < bill.amount_expected:
            bill.status = PaymentStatuses.PARTIALLY_PAID.value
            bill.save()
        else:
            bill.status = PaymentStatuses.PENDING.value
            bill.save()

        return redirect("pending-bills")
    return render(request, "water_bills/collect_pending_bill.html")