import csv
from apps.tenants.models import Tenant
from apps.users.models import User
from apps.properties.models import PropertyUnit
from django.db import transaction
from datetime import datetime

def construct_date(date_str):
    split_date = date_str.split("/")
    return datetime(int(split_date[2]), int(split_date[0]), int(split_date[1]))

@transaction.atomic
def load_tenants():
    tenants = []

    with open('tenants.csv', 'r') as file:
        tenants = list(csv.DictReader(file))

    for tenant in tenants:
        unit_number = tenant.get("unit_number")
        lease_date_str = tenant.get("lease_date")
        lease_date = construct_date(lease_date_str)

        unit = PropertyUnit.objects.filter(name=unit_number).first()
        if not unit:
            print(f"Unit {unit_number} not found")
            continue

        user = User.objects.create(
            first_name=tenant['first_name'],
            last_name=tenant['last_name'],
            email=tenant['email'],
            phone=tenant['phone_number'],
            password="123456",
            username=tenant['email'],
            city="Nakuru",
            state="Nakuru County",
            country="Kenya",
            zip_code="20100",
            address="Milimani Estate",
            
        )
        user.set_password("123456")
        user.save()

        tenant = Tenant.objects.create(
            user=user,
            move_in_date=construct_date(tenant['lease_date']),
            lease_date=construct_date(tenant['lease_date']),
            status="Active",
            lease_duration="1 Year",
            renews_every="1 Year",
        )
      
        unit.is_occupied = True
        unit.tenant = tenant
        unit.status = "Occupied"
        unit.save()

        print(f"Tenant {tenant.user.first_name} {tenant.user.last_name} created")