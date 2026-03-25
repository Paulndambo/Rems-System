from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from datetime import datetime
from decimal import Decimal
from django.views.generic import ListView
from django.http import JsonResponse
from django.db.models import Q
from django.db import transaction
from django.core.paginator import Paginator
from django.contrib.auth.mixins import LoginRequiredMixin

from apps.core.models import UserAction
from apps.properties.models import Property, PropertyUnit, MaintenanceRequest

"""Maintenance Requests"""


class MaintenanceListView(LoginRequiredMixin, ListView):
    model = MaintenanceRequest
    template_name = "properties/maintenance_requests/maintenance_requests.html"
    context_object_name = "maintenance_requests"
    paginate_by = 9

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query) | Q(title__icontains=search_query)
            )

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["search_query"] = self.request.GET.get("search", "")
        context["units"] = PropertyUnit.objects.all()
        context["priority_levels"] = ["High", "Medium", "Low"]
        context["maintenance_statuses"] = ["Pending", "In Progress", "Completed"]
        return context


@login_required
def new_maintenance_request(request):
    if request.method == "POST":
        unit_id = request.POST.get("unit")
        property_id = request.POST.get("property")
        
        unit = PropertyUnit.objects.filter(id=unit_id).first() if unit_id else None
        property = Property.objects.filter(id=property_id).first() if property_id else None

        title = request.POST.get("title")
        priority = request.POST.get("priority")
        description = request.POST.get("description")
        status = request.POST.get("status")
        cost = request.POST.get("cost")

        MaintenanceRequest.objects.create(
            title=title,
            property=unit.property if unit else property,
            unit=unit,
            status=status,
            cost=Decimal(cost),
            description=description,
            priority=priority,
        )
        UserAction.objects.create(
            user=request.user,
            action=f"New Maintenance Request Added",
            action_type="Created",
            description=f"Added Maintenance Request with Title: {title}"
        )
        return redirect("maintenance-requests")
    return render(
        request, "properties/maintenance_requests/new_maintenance_request.html",
        {
            "properties": Property.objects.all(),
            "units": PropertyUnit.objects.all(),
            "priority_levels": ["High", "Medium", "Low"],
            "maintenance_statuses": ["Pending", "In Progress", "Completed"]
        }
    )


@login_required
def edit_maintenance_request(request):
    maintenance_request_object = MaintenanceRequest.objects.filter(id=request.GET.get("maintenance_id")).first()

    if request.method == "POST":
        maintenance_request_id = request.POST.get("request_id")
        title = request.POST.get("title")
        description = request.POST.get("description")
        status = request.POST.get("status")
        status = request.POST.get("status")
        priority = request.POST.get("priority")
        cost = request.POST.get("cost")
        unit_id = request.POST.get("unit")
        property_id = request.POST.get("property")

        
        unit = PropertyUnit.objects.filter(id=unit_id).first() if unit_id else None
        property = Property.objects.filter(id=property_id).first() if property_id else None        

        maintenance_request = MaintenanceRequest.objects.get(id=maintenance_request_id)

        maintenance_request.title = title
        maintenance_request.description = description
        maintenance_request.status = status
        maintenance_request.priority = priority
        maintenance_request.cost = Decimal(cost)
        maintenance_request.unit = unit
        maintenance_request.property = unit.property if unit else property
        maintenance_request.save()
        UserAction.objects.create(
            user=request.user,
            action=f"Maintenance Request Updated",
            action_type="Updated",
            description=f"Updated Maintenance Request with ID: {maintenance_request_id}, Title: {maintenance_request.title}"
        )
        return redirect("maintenance-requests")
    return render(
        request, "properties/maintenance_requests/edit_maintenance_request.html",
        {
            "maintenance_request": maintenance_request_object,
            "properties": Property.objects.all(),
            "units": PropertyUnit.objects.all(),
            "priority_levels": ["High", "Medium", "Low"],
            "maintenance_statuses": ["Pending", "In Progress", "Completed"]
        }
    )


@login_required
def delete_maintenance_request(request):
    maintenance_request_object = MaintenanceRequest.objects.filter(id=request.GET.get("maintenance_id")).first()

    if request.method == "POST":
        maintenance_request_id = request.POST.get("request_id")
        maintenance_request = MaintenanceRequest.objects.get(id=maintenance_request_id)
        UserAction.objects.create(
            user=request.user,
            action=f"Maintenance Request Deleted",
            action_type="Deleted",
            description=f"Deleted Maintenance Request with ID: {maintenance_request_id}, Title: {maintenance_request.title}"
        )
        maintenance_request.delete()
        return redirect("maintenance-requests")
    return render(
        request, "properties/maintenance_requests/delete_maintenance_request.html",
        {
            "maintenance_request": maintenance_request_object
        }
    )
