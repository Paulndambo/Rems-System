from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Avg, Sum
from django.views.generic import ListView
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.core.paginator import Paginator

from apps.tenants.models import Tenant, TenantNextOfKin
from apps.properties.models import PropertyUnit, WaterBill
from apps.payments.models import TenantPayment
from apps.users.models import User
from apps.core.constants import LEASE_DURATIONS, MARITAL_STATUSES

# from apps.payments.models import WaterBill, TenantMonthlyBill
# Create your views here.


class TenantListView(LoginRequiredMixin, ListView):
    model = Tenant
    template_name = "tenants/tenants.html"
    context_object_name = "tenants"
    paginate_by = 9

    # Optional: You can specify where to redirect if user is not logged in
    # login_url = '/login/'  # Add this if you want to specify a custom login URL

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query)
                | Q(user__first_name__icontains=search_query)
                | Q(user__last_name__icontains=search_query)
                | Q(user__phone__icontains=search_query)
                | Q(user__email__icontains=search_query)
                | Q(user__id_number__icontains=search_query)
                | Q(move_in_date__icontains=search_query)
                | Q(lease_duration__icontains=search_query)
                | Q(lease_date__icontains=search_query)
                | Q(occupation__icontains=search_query)
                | Q(status__icontains=search_query)
            )

        return queryset.order_by("propertyunit__name")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["lease_durations"] = LEASE_DURATIONS
        context["marital_statuses"] = MARITAL_STATUSES
        context["units"] = PropertyUnit.objects.filter(is_occupied=False)
        return context


@login_required
def tenant_detail(request, pk):
    tenant = get_object_or_404(Tenant, pk=pk)

    # Get all the data
    all_units = PropertyUnit.objects.filter(tenant=tenant)
    all_water_bills = WaterBill.objects.filter(unit__tenant=tenant)
    all_payments = TenantPayment.objects.filter(tenant=tenant).order_by("-created_at")

    # Set up pagination
    units_paginator = Paginator(all_units, 5)  # Show 10 units per page
    water_bills_paginator = Paginator(
        all_water_bills, 5
    )  # Show 10 water bills per page
    payments_paginator = Paginator(all_payments, 5)  # Show 10 payments per page

    # Get page numbers from request
    units_page = request.GET.get("units_page", 1)
    water_page = request.GET.get("water_page", 1)
    payments_page = request.GET.get("payments_page", 1)

    # Get the page objects
    units = units_paginator.get_page(units_page)
    water_bills = water_bills_paginator.get_page(water_page)
    payments = payments_paginator.get_page(payments_page)

    # Calculate totals (assuming these calculations were already present)
    total_expected_rent = (
        tenant.tenantrentpayments.aggregate(total_expected=Sum("amount_expected"))[
            "total_expected"
        ]
        or 0
    )
    total_water_bill = (
        all_water_bills.aggregate(total_amount=Sum("amount"))["total_amount"] or 0
    )
    total_rent_paid = (
        tenant.tenantrentpayments.aggregate(total_amount=Sum("amount_paid"))[
            "total_amount"
        ]
        or 0
    )
    total_water_paid = (
        all_water_bills.aggregate(total_amount=Sum("amount_paid"))["total_amount"] or 0
    )
    total_debt = (
        total_expected_rent + total_water_bill - (total_rent_paid + total_water_paid)
        if (total_expected_rent and total_water_bill)
        else 0
    )

    context = {
        "tenant": tenant,
        "units": units,
        "water_bills": water_bills,
        "payments": payments,
        "total_rent_paid": round(total_rent_paid, 2) if total_rent_paid else 0,
        "total_water_paid": round(total_water_paid, 2) if total_water_paid else 0,
        "total_debt": round(total_debt, 2) if total_debt else 0,
        "total_water_bill": round(total_water_bill, 2) if total_water_bill else 0,
        "total_expected_rent": (
            round(total_expected_rent, 2) if total_expected_rent else 0
        ),
    }

    return render(request, "tenants/tenant_details.html", context)


@login_required
@transaction.atomic
def new_tenant(request):
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        id_number = request.POST.get("id_number")
        gender = request.POST.get("gender")
        move_in_date = request.POST.get("move_in_date")
        lease_duration = request.POST.get("lease_duration")
        lease_date = request.POST.get("lease_date")
        marital_status = request.POST.get("marital_status")

        rental_unit = request.POST.get("rental_unit")
        unit = PropertyUnit.objects.get(id=rental_unit)

        user = User.objects.create(
            first_name=first_name,
            last_name=last_name,
            email=email if email else f"{first_name}.{last_name}@gmail.com",
            phone=phone,
            id_number=id_number,
            gender=gender,
            username=email if email else f"{first_name}.{last_name}",
            marital_status=marital_status,
            role="Tenant",
        )

        user.set_password("1234")
        user.save()

        tenant = Tenant.objects.create(
            user=user,
            move_in_date=move_in_date,
            lease_duration=lease_duration,
            lease_date=lease_date,
            status="Active",
            renews_every=lease_duration,
        )
        unit.tenant = tenant
        unit.is_occupied = True
        unit.save()
        return redirect("tenants")
    return render(request, "tenants/new_tenant.html")


@login_required
@transaction.atomic
def edit_tenant(request):
    if request.method == "POST":
        tenant_id = request.POST.get("tenant_id")
        tenant = Tenant.objects.get(id=tenant_id)
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")
        phone = request.POST.get("phone")
        id_number = request.POST.get("id_number")
        gender = request.POST.get("gender")
        move_in_date = request.POST.get("move_in_date")
        lease_duration = request.POST.get("lease_duration")
        lease_date = request.POST.get("lease_date")
        marital_status = request.POST.get("marital_status")

        rental_unit = request.POST.get("rental_unit")
        unit = PropertyUnit.objects.filter(id=rental_unit).first()

        tenant.user.first_name = first_name
        tenant.user.last_name = last_name
        tenant.user.email = email
        tenant.user.phone = phone
        tenant.user.id_number = id_number
        tenant.user.gender = gender
        tenant.move_in_date = move_in_date
        tenant.lease_duration = lease_duration
        tenant.user.marital_status = marital_status
        tenant.renews_every = lease_duration
        tenant.lease_date = lease_date

        tenant.user.save()
        tenant.save()

        if unit:
            unit.tenant = tenant
            unit.is_occupied = True
            unit.save()
        return redirect("tenants")
    return render(request, "tenants/edit_tenant.html", {"tenant": tenant})


@login_required
@transaction.atomic
def delete_tenant(request):
    if request.method == "POST":
        tenant_id = request.POST.get("tenant_id")
        unit = PropertyUnit.objects.filter(tenant=tenant_id).first()
        if unit:
            unit.tenant = None
            unit.is_occupied = False
            unit.save()
        Tenant.objects.get(id=tenant_id).delete()
        return redirect("tenants")
    return render(request, "tenants/delete_tenant.html")
