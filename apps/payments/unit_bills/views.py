from datetime import datetime
from decimal import Decimal
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
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
import json
from apps.properties.models import PropertyUnit, Property
from apps.core.models import Month, Year
from apps.payments.models import GarbageBill, GarbageBillPayment, UnitMonthBill


class UnitMonthBillsView(ListView):
    model = UnitMonthBill
    template_name = "unit_bills/unit_bills.html"
    context_object_name = "unit_bills"


    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query)
                | Q(unit__name__icontains=search_query)
                | Q(unit__property__name__icontains=search_query)
                | Q(tenant__user__first_name__icontains=search_query)
                | Q(tenant__user__last_name__icontains=search_query)
            )
        return queryset.order_by("-created_at")


    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
