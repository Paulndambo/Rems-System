from django.urls import path

from apps.tenants.views import tenants, tenant_detail, new_tenant, edit_tenant, delete_tenant

urlpatterns = [
    path('', tenants, name='tenants'),
    path('<int:pk>/', tenant_detail, name='tenant-detail'),
    path('new-tenant/', new_tenant, name='new-tenant'),
    path('edit-tenant/', edit_tenant, name='edit-tenant'),
    path('delete-tenant/', delete_tenant, name='delete-tenant'),
]