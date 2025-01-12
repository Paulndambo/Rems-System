from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('monthly-rent-report/', views.monthly_rent_report, name='monthly-rent-report'),
    path('expenses-report/', views.expenses_report, name='expenses-report'),
    path('tenant-payments-report/', views.tenant_payments_report, name='tenant-payments-report'),
    path('water-bills-report/', views.water_bills_report, name='water-bills-report'),
    path('water-bills-payments-report/', views.water_bills_payments_report, name='water-bills-payments-report'),
]