from django.urls import path

from apps.properties.views import (
    properties, 
    new_property, 
    edit_property, 
    delete_property, 
    property_detail, 
    property_units, 
    new_property_unit, 
    edit_property_unit, 
    delete_property_unit, 
    property_unit_detail,
    maintenance_requests,
    new_maintenance_request,
    edit_maintenance_request,
    delete_maintenance_request
)

urlpatterns = [
    path('', properties, name='properties'),
    path('<int:id>/', property_detail, name='property-detail'),
    path('new-property/', new_property, name='new-property'),
    path('edit-property/', edit_property, name='edit-property'),
    path('delete-property/', delete_property, name='delete-property'),
    path('units/', property_units, name='units'),
    path('unit/<int:id>/', property_unit_detail, name='unit-detail'),
    path('new-unit/', new_property_unit, name='new-unit'),
    path('edit-unit/', edit_property_unit, name='edit-unit'),
    path('delete-unit/', delete_property_unit, name='delete-unit'),

    path('maintenance-requests/', maintenance_requests, name='maintenance-requests'),
    path('new-maintenance-request/', new_maintenance_request, name='new-maintenance-request'),
    path('edit-maintenance-request/', edit_maintenance_request, name='edit-maintenance-request'),
    path('delete-maintenance-request/', delete_maintenance_request, name='delete-maintenance-request'),
]