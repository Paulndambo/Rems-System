from django.contrib import admin

from apps.properties.models import Property, PropertyUnit, WaterBill


# Register your models here.
@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "owner", "city", "country", "units", "house_manager")


@admin.register(PropertyUnit)
class PropertyUnitAdmin(admin.ModelAdmin):
    list_display = ("id", "tenant", "name", "property", "rent", "is_occupied")


@admin.register(WaterBill)
class WaterBillAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "unit",
        "month",
        "year",
        "previous_reading",
        "current_reading",
        "units_consumed",
        "reading_date",
        "due_date",
        "amount",
        "status",
    )
    list_filter = ("year", "unit")
