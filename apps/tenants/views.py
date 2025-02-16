from django.shortcuts import render, redirect
from django.db.models import Avg, Sum
from django.views.generic import ListView
from django.db.models import Q

from apps.tenants.models import Tenant, TenantNextOfKin
from apps.properties.models import PropertyUnit
from apps.users.models import User
from apps.core.constants import LEASE_DURATIONS, MARITAL_STATUSES
#from apps.payments.models import WaterBill, TenantMonthlyBill
# Create your views here.
def tenants(request):
    tenants = Tenant.objects.all().order_by('-created_at')
    units = PropertyUnit.objects.filter(is_occupied=False)
    context = {
        'tenants': tenants,
        'units': units,
        'lease_durations': LEASE_DURATIONS,
        'marital_statuses': MARITAL_STATUSES
    }
    return render(request, 'tenants/tenants.html', context)


class TenantListView(ListView):
    model = Tenant
    template_name = "tenants/tenants.html"
    context_object_name = "tenants"
    paginate_by = 9

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get("search", "")

        print(f"You are searching for {search_query}")

        if search_query:
            queryset = queryset.filter(
                Q(id__icontains=search_query)
                | Q(user__first_name__icontains=search_query)
                | Q(user__last_name__icontains=search_query)
                | Q(user__phone__icontains=search_query)
                | Q(user__email__icontains=search_query)
                | Q(user__id_number__icontains=search_query)
            
                | Q(move_in_date__icontains=search_query)
                | Q(lease_duration__icontains=search_query)
                | Q(lease_date__icontains=search_query)
                | Q(occupation__icontains=search_query)
                | Q(status__icontains=search_query)
            )

        return queryset.order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['lease_durations'] = LEASE_DURATIONS
        context['marital_statuses'] = MARITAL_STATUSES
        return context


def tenant_detail(request, pk):

    tenant = Tenant.objects.get(pk=pk)
    next_of_kin = TenantNextOfKin.objects.filter(tenant=tenant)

    units = PropertyUnit.objects.filter(tenant=tenant)
    water_bills = tenant.tenantwaterbills.all().order_by('-created_at')
    #payments = TenantMonthlyBill.objects.filter(tenant=tenant).order_by('-created_at')
    print(water_bills)
    payments = tenant.tenantpayments.all().order_by('-created_at')


    total_expected_rent = tenant.tenantrentpayments.aggregate(total_expected=Sum('amount_expected'))['total_expected'] if len(tenant.tenantrentpayments.all()) > 0 else 0
    total_water_bill = water_bills.aggregate(total_amount=Sum('amount'))['total_amount'] if len(water_bills) > 0 else 0


    total_water_paid = water_bills.aggregate(total_amount=Sum('amount_paid'))['total_amount'] if len(water_bills) > 0 else 0
    total_rent_paid = tenant.tenantrentpayments.aggregate(total_amount=Sum('amount_paid'))['total_amount'] if len(tenant.tenantrentpayments.all()) > 0 else 0

    total_bill = total_expected_rent + total_water_bill if (total_expected_rent and total_expected_rent ) else 0
    total_paid = total_rent_paid + total_water_paid if (total_rent_paid and total_water_paid) else 0
    total_debt = total_bill - total_paid if (total_bill and total_paid) else 0

    context = {
        'tenant': tenant,
        'next_of_kin': next_of_kin,
        'units': units,
        'water_bills': water_bills,
        'payments': payments,
        'total_water_bill': total_water_bill if total_water_bill else 0,
        'total_rent_paid': total_rent_paid if total_rent_paid else 0,
        'total_water_paid': total_water_paid if total_water_paid else 0,
        'total_bill': round(total_bill, 2) if total_bill else 0,
        'total_paid': round(total_paid, 2) if total_paid else 0,
        'total_debt': round(total_debt, 2) if total_debt else 0
    }
    return render(request, 'tenants/tenant_details.html', context)


def new_tenant(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        id_number = request.POST.get('id_number')
        gender = request.POST.get("gender")
        move_in_date = request.POST.get('move_in_date')
        lease_duration = request.POST.get('lease_duration')
        lease_date = request.POST.get('lease_date')
        marital_status = request.POST.get('marital_status')

        user = User.objects.create(
            first_name=first_name, 
            last_name=last_name, 
            email=email if email else f"{first_name}.{last_name}@gmail.com", 
            phone=phone, 
            id_number=id_number,
            gender=gender,
            username=email if email else f"{first_name}.{last_name}",
            marital_status=marital_status,
            role='Tenant',
        )

        user.set_password('1234')
        user.save()

        Tenant.objects.create(
            user=user,
            move_in_date=move_in_date,
            lease_duration=lease_duration,
            lease_date=lease_date,
            status='Active',
            renews_every=lease_duration
        )
        return redirect('tenants')
    return render(request, 'tenants/new_tenant.html')


def edit_tenant(request):
    if request.method == 'POST':
        tenant_id = request.POST.get('tenant_id')
        tenant = Tenant.objects.get(id=tenant_id)
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        id_number = request.POST.get('id_number')
        gender = request.POST.get("gender")
        move_in_date = request.POST.get('move_in_date')
        lease_duration = request.POST.get('lease_duration')
        lease_date = request.POST.get('lease_date')
        marital_status = request.POST.get('marital_status')
        

        tenant.user.first_name = first_name
        tenant.user.last_name = last_name
        tenant.user.email = email
        tenant.user.phone = phone
        tenant.user.id_number = id_number
        tenant.user.gender = gender
        tenant.move_in_date = move_in_date
        tenant.lease_duration = lease_duration
        tenant.user.marital_status = marital_status
        tenant.renews_every = lease_duration
        tenant.lease_date = lease_date


        tenant.user.save()
        tenant.save()
        return redirect('tenants')
    return render(request, 'tenants/edit_tenant.html', {'tenant': tenant})


def delete_tenant(request):
    if request.method == "POST":
        tenant_id = request.POST.get("tenant_id")
        Tenant.objects.get(id=tenant_id).delete()
        return redirect("tenants")
    return render(request, 'tenants/delete_tenant.html')