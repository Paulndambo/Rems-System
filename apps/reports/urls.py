from django.urls import path
from . import views

app_name = "reports"

urlpatterns = [
    path("monthly-rent-report/", views.monthly_rent_report, name="monthly-rent-report"),
    path("water-bills-report/", views.water_payments_report, name="water-bills-report"),
]
