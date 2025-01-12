from django.shortcuts import render, redirect
from django.db.models import Avg

from apps.tenants.models import Tenant, TenantNextOfKin
from apps.properties.models import PropertyUnit
from apps.users.models import User
from apps.core.constants import LEASE_DURATIONS 
#from apps.payments.models import WaterBill, TenantMonthlyBill
# Create your views here.
def tenants(request):
    tenants = Tenant.objects.all().order_by('-created_at')
    units = PropertyUnit.objects.filter(is_occupied=False)
    context = {
        'tenants': tenants,
        'units': units,
        'lease_durations': LEASE_DURATIONS
    }
    return render(request, 'tenants/tenants.html', context)


def tenant_detail(request, pk):
    tenant = Tenant.objects.get(pk=pk)
    next_of_kin = TenantNextOfKin.objects.filter(tenant=tenant)

    units = PropertyUnit.objects.filter(tenant=tenant)
    water_bills = tenant.tenantwaterbills.all().order_by('-created_at')
    #payments = TenantMonthlyBill.objects.filter(tenant=tenant).order_by('-created_at')
    print(water_bills)
    payments = tenant.tenantpayments.all().order_by('-created_at')

    average_water_bill = water_bills.aggregate(avg_amount=Avg('amount'))['avg_amount']

    total_expected_rent = tenant.tenantrentpayments.aggregate(total_expected=Avg('amount_expected'))['total_expected']
    total_water_bill = water_bills.aggregate(total_amount=Avg('amount'))['total_amount']


    total_water_paid = water_bills.aggregate(total_amount=Avg('amount_paid'))['total_amount']
    total_rent_paid = tenant.tenantrentpayments.aggregate(total_amount=Avg('amount_paid'))['total_amount']

    total_bill = total_expected_rent + total_water_bill
    total_paid = total_rent_paid + total_water_paid
    total_debt = total_bill - total_paid

    context = {
        'tenant': tenant,
        'next_of_kin': next_of_kin,
        'units': units,
        'water_bills': water_bills,
        'payments': payments,
        'average_water_bill': average_water_bill,
        'total_rent_paid': total_rent_paid,
        'total_bill': total_bill,
        'total_paid': total_paid,
        'total_debt': total_debt
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
        unit_assigned = request.POST.get('unit_assigned')
        move_in_date = request.POST.get('move_in_date')
        lease_duration = request.POST.get('lease_duration')
        lease_date = request.POST.get('lease_date')
        occupation = request.POST.get('occupation')

        user = User.objects.create(
            first_name=first_name, 
            last_name=last_name, 
            email=email, 
            phone=phone, 
            id_number=id_number,
            gender=gender,
            username=email,
            role='Tenant',
        )

        user.set_password('1234')
        user.save()

        tenant = Tenant.objects.create(
            user=user,
            move_in_date=move_in_date,
            lease_duration=lease_duration,
            lease_date=lease_date,
            occupation=occupation,
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
        unit_assigned = request.POST.get('unit_assigned')
        move_in_date = request.POST.get('move_in_date')
        lease_duration = request.POST.get('lease_duration')
        lease_date = request.POST.get('lease_date')
        occupation = request.POST.get('occupation')
        

        tenant.user.first_name = first_name
        tenant.user.last_name = last_name
        tenant.user.email = email
        tenant.user.phone = phone
        tenant.user.id_number = id_number
        tenant.user.gender = gender
        tenant.unit_assigned = unit_assigned
        tenant.move_in_date = move_in_date
        tenant.lease_duration = lease_duration
        tenant.occupation = occupation
        tenant.renews_every = lease_duration


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