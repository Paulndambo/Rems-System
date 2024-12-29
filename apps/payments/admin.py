from django.contrib import admin

from apps.payments.models import WaterBill
# Register your models here.
@admin.register(WaterBill)
class WaterBillAdmin(admin.ModelAdmin):
    list_display = ['id', 'unit', 'month', 'year', 'units', 'amount', 'created_at', 'updated_at', 'is_active']
    
