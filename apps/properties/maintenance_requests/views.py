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

from apps.properties.models import PropertyUnit, MaintenanceRequest

"""Maintenance Requests"""
class MaintenanceListView(ListView):
    model = MaintenanceRequest
    template_name = "properties/maintenance_requests/maintenance_requests.html"
    context_object_name = "maintenance_requests"
    paginate_by = 9

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query) |
                Q(title__icontains=search_query) 
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
        unit_id = request.POST.get('unit')
        unit = PropertyUnit.objects.get(id=unit_id)

        title = request.POST.get('title')
        priority = request.POST.get('priority')
        description = request.POST.get('description')

        MaintenanceRequest.objects.create(
            title=title,
            property=unit.property, 
            unit=unit, 
            description=description,
            priority=priority
        )
        return redirect("unit-detail", id=unit_id)
    return render(request, 'properties/maintenance_requests/new_maintenance_request.html')


@login_required
def edit_maintenance_request(request):
    if request.method == "POST":
        maintenance_request_id = request.POST.get('request_id')
        title = request.POST.get('title')
        description = request.POST.get('description')
        status = request.POST.get('status')
       
        priority = request.POST.get('priority')
        cost = request.POST.get('cost')

        maintenance_request = MaintenanceRequest.objects.get(id=maintenance_request_id)
        maintenance_request.title = title
        maintenance_request.description = description
        maintenance_request.status = status
        maintenance_request.priority = priority
        maintenance_request.cost = cost
        maintenance_request.save()
        return redirect("maintenance-requests")
    return render(request, 'properties/maintenance_requests/edit_maintenance_request.html')


@login_required
def delete_maintenance_request(request):
    if request.method == "POST":
        maintenance_request_id = request.POST.get('request_id')
        MaintenanceRequest.objects.get(id=maintenance_request_id).delete()
        return redirect("maintenance-requests")
    return render(request, 'properties/maintenance_requests/delete_maintenance_request.html')
