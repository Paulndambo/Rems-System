from django.contrib import admin

from apps.core.models import WaterPrice
# Register your models here.
@admin.register(WaterPrice)
class WaterPriceAdmin(admin.ModelAdmin):
    list_display = ['id', 'unit_price', 'created_at', 'updated_at', 'is_active']
    
