from django.contrib import admin
from .models import RentPayment, TenantPayment, RentBill

# Register your models here.
@admin.register(RentPayment)
class RentPaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "rent_bill", "amount_paid", "payment_date", "payment_method"]

@admin.register(RentBill)
class RentBillAdmin(admin.ModelAdmin):
    list_display = ["id", "tenant", "unit", "amount_expected", "amount_paid", "due_date", "status", "fully_paid"]
    


@admin.register(TenantPayment)
class TenantPaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "tenant", "unit", "amount_paid", "payment_date", "payment_method"]