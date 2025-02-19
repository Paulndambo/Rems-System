from django.urls import path

from apps.properties.views import (
    properties, 
    new_property, 
    edit_property, 
    delete_property, 
    property_detail, 

    new_property_unit, 
    edit_property_unit, 
    delete_property_unit, 
    property_unit_detail,
    maintenance_requests,
    new_maintenance_request,
    edit_maintenance_request,
    delete_maintenance_request,
    assign_tenant,
    view_water_bill,
   
    edit_water_bill,
    delete_water_bill,
    WaterBillListView,
    PropertyUnitListView
)
from apps.properties.water_bills.views import new_water_bill

urlpatterns = [
    path('', properties, name='properties'),
    path('<int:id>/', property_detail, name='property-detail'),
    path('new-property/', new_property, name='new-property'),
    path('edit-property/', edit_property, name='edit-property'),
    path('delete-property/', delete_property, name='delete-property'),
    path('units/', PropertyUnitListView.as_view(), name='units'),
    path('unit/<int:id>/', property_unit_detail, name='unit-detail'),
    path('new-unit/', new_property_unit, name='new-unit'),
    path('edit-unit/', edit_property_unit, name='edit-unit'),
    path('delete-unit/', delete_property_unit, name='delete-unit'),
    path('assign-tenant/', assign_tenant, name='assign-tenant'),

    path('new-water-bill/', new_water_bill, name='new-water-bill'),
    path('edit-water-bill/', edit_water_bill, name='edit-water-bill'),
    path('delete-water-bill/', delete_water_bill, name='delete-water-bill'),
    path('water-bills/', WaterBillListView.as_view(), name='water-bills'),
    path('view-water-bill/<int:id>/', view_water_bill, name='view-water-bill'),

    path('maintenance-requests/', maintenance_requests, name='maintenance-requests'),
    path('new-maintenance-request/', new_maintenance_request, name='new-maintenance-request'),
    path('edit-maintenance-request/', edit_maintenance_request, name='edit-maintenance-request'),
    path('delete-maintenance-request/', delete_maintenance_request, name='delete-maintenance-request'),
]