from django.urls import path

from apps.payments.views import water_bills, new_bill, edit_bill, delete_bill

urlpatterns = [
    path('water-bills/', water_bills, name='water-bills'),
    path('new-water-bill/', new_bill, name='new-water-bill'),
    path('edit-water-bill/', edit_bill, name='edit-water-bill'),
    path('delete-water-bill/', delete_bill, name='delete-water-bill'),
]