from django.contrib import admin
from .models import RentPayment, TenantPayment, RentBill, WaterBillPayment, Expense, GarbageBill, UnitMonthBill

# Register your models here.

@admin.register(UnitMonthBill)
class UnitMonthBillAdmin(admin.ModelAdmin):
    list_display = ["id", "unit", "tenant", "rent_amount", "water_amount", "garbage_amount", "amount_expected"]

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

@admin.register(GarbageBill)
class GarbageBillAdmin(admin.ModelAdmin):
    list_display = ["id", "unit", "tenant", "amount_expected", "amount_paid", "due_date", "status", "fully_paid"]
