from django.contrib import admin
from .models import RentPayment, TenantPayment, RentBill, WaterBillPayment, Expense, GarbageBill, UnitMonthBill, GarbageBillPayment, SecurityDeposit, SecurityDepositPayment

# Register your models here.

@admin.register(UnitMonthBill)
class UnitMonthBillAdmin(admin.ModelAdmin):
    list_display = ["id", "unit", 'month', 'year', "tenant", "rent_amount", "water_amount", "garbage_amount", "amount_expected", "amount_paid", "balance", "fully_paid"]
    list_filter = ('year', 'month', 'unit')

@admin.register(RentPayment)
class RentPaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "rent_bill", "amount_paid", "payment_date", "payment_method"]
    list_filter = ("rent_bill__unit_bill__unit", "rent_bill__unit_bill__month", "rent_bill__unit_bill__year")


@admin.register(RentBill)
class RentBillAdmin(admin.ModelAdmin):
    list_display = ["id", "tenant", "unit", "amount_expected", "amount_paid", "due_date", "status", "fully_paid"]
    list_filter = ("year", "month", "unit")
    

@admin.register(TenantPayment)
class TenantPaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "tenant", "unit", "amount_paid", "payment_date", "payment_method"]
    list_filter = ("unit", "month", "year")

@admin.register(WaterBillPayment)
class WaterBillPaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "tenant", "water_bill", "amount_paid", "payment_date", "payment_method"]
    list_filter = ("water_bill__unit_bill__unit", "water_bill__unit_bill__month", "water_bill__unit_bill__year")

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "property", "unit", "amount", "expense_type", "spend_on"]

@admin.register(GarbageBill)
class GarbageBillAdmin(admin.ModelAdmin):
    list_display = ["id", "unit", "tenant", "amount_expected", "amount_paid", "due_date", "status", "fully_paid"]
    list_filter = ("unit_bill__unit", "unit_bill__month", "unit_bill__year")

@admin.register(GarbageBillPayment)
class GarbageBillPaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "garbage_bill", "amount_paid", "payment_date", "payment_method"]
    list_filter = ("garbage_bill__unit_bill__unit", "garbage_bill__unit_bill__month", "garbage_bill__unit_bill__year")

@admin.register(SecurityDeposit)
class SecurityDepositAdmin(admin.ModelAdmin):
    list_display = ["id", "unit", "tenant", "amount_expected", "amount_paid", "status", "fully_paid"]
    #list_filter = ("unit", "month", "year")

@admin.register(SecurityDepositPayment)
class SecurityDepositPaymentAdmin(admin.ModelAdmin):
    list_display = ["id", "security_deposit", "amount_paid", "payment_date", "payment_method"]
    #list_filter = ("security_deposit__unit", "security_deposit__month", "security_deposit__year")
