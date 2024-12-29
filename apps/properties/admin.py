from django.contrib import admin

from apps.properties.models import Property, PropertyUnit
# Register your models here.
@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner', 'city', 'country', 'units')
   

@admin.register(PropertyUnit)
class PropertyUnitAdmin(admin.ModelAdmin):
    list_display = ('id', 'tenant', 'name', 'property', 'rent', 'is_occupied')