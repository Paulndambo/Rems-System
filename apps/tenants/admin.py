from django.contrib import admin

from apps.tenants.models import Tenant, TenantNextOfKin
# Register your models here.
@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'lease_date', 'move_in_date', 'status']
   

# admin.site.register(TenantNextOfKin)

