from django.db import transaction
from datetime import date
from apps.properties.models import PropertyUnit, WaterBill
from apps.tenants.models import Tenant
from apps.users.models import User
from apps.payments.models import UnitMonthBill, SecurityDeposit, TenantPayment, GarbageBill

class OnboardTenantMixin(object):
    def __init__(self, 
            first_name: str, 
            last_name: str, 
            email: str, 
            phone: str, 
            id_number: str, 
            gender: str, 
            move_in_date: date, 
            lease_duration: str, 
            lease_date: date, 
            marital_status: str, 
            rental_unit: int, 
            occupation: str
        ):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.id_number = id_number
        self.gender = gender
        self.move_in_date = move_in_date
        self.lease_duration = lease_duration
        self.lease_date = lease_date
        self.marital_status = marital_status
        self.rental_unit = rental_unit
        self.occupation = occupation
        
    @transaction.atomic
    def run(self):
        self.__process_tenant()
    
    def __process_tenant(self):
        unit = PropertyUnit.objects.get(id=self.rental_unit)
        
        user = User.objects.create(
            first_name=self.first_name,
            last_name=self.last_name,
            email=self.email if self.email else f"{self.first_name}.{self.last_name}@gmail.com",
            phone=self.phone,
            id_number=self.id_number,
            gender=self.gender,
            username=self.email if self.email else f"{self.first_name}.{self.last_name}",
            marital_status=self.marital_status,
            role="Tenant",
        )
        
        user.set_password("1234")
        user.save()

        tenant = Tenant.objects.create(
            user=user,
            move_in_date=self.move_in_date,
            lease_duration=self.lease_duration,
            lease_date=self.lease_date,
            status="Active",
            renews_every=self.lease_duration,
        )
        
        
        #WaterBill.objects.filter(unit=unit).update(unit=None)
        #UnitMonthBill.objects.filter(unit=unit).update(unit=None)
        #TenantPayment.objects.filter(unit=unit).update(unit=None)
        #GarbageBill.objects.filter(unit=unit).update(unit=None)
        
        unit.tenant = tenant
        unit.is_occupied = True
        unit.save()
        
        SecurityDeposit.objects.create(
            tenant=tenant,
            unit=unit,
            amount_expected=unit.security_deposit,
        )
 
@transaction.atomic       
def clean_up_unit(unit: PropertyUnit):
    print("**************Starting Unit Cleanup**************")
    WaterBill.objects.filter(unit=unit).update(unit=None)
    UnitMonthBill.objects.filter(unit=unit).update(unit=None)
    TenantPayment.objects.filter(unit=unit).update(unit=None)
    GarbageBill.objects.filter(unit=unit).update(unit=None)
    print("**************Finished Unit Cleanup**************")
    