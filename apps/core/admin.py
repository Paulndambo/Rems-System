from django.contrib import admin

from apps.core.models import WaterPrice, Year, Month, UserAction


# Register your models here.
@admin.register(WaterPrice)
class WaterPriceAdmin(admin.ModelAdmin):
    list_display = ["id", "unit_price", "created_at", "updated_at", "is_active"]


@admin.register(Year)
class YearAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "created_at", "updated_at", "is_active"]


@admin.register(Month)
class MonthAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "year", "created_at", "updated_at", "is_active"]

@admin.register(UserAction)
class UserActionAdmin(admin.ModelAdmin):
    list_display = ["id", "action_type", "user", "created_at", "updated_at", "is_active"]