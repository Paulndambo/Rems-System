from django.contrib import admin
from .models import RentPayment, TenantPayment, RentBill, WaterBillPayment, Expense

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

@admin.register(WaterBillPayment)
class WaterBillPaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "tenant", "water_bill", "amount_paid", "payment_date", "payment_method"]

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "amount", "expense_type", "spend_on"]