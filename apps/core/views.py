from django.db import models
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.properties.models import Property
from apps.tenants.models import Tenant
from apps.payments.models import WaterBill, TenantPayment
# Create your views here.
@login_required
def home(request):
    tenants_count = Tenant.objects.count()
    properties_count = Property.objects.count()
    total_revenue = TenantPayment.objects.aggregate(total_amount=models.Sum('amount_paid'))['total_amount']

    context = {
        'tenants_count': tenants_count,
        'properties_count': properties_count, 
        'total_revenue': total_revenue if total_revenue is not None else 0
    }
    return render(request, 'home.html', context)