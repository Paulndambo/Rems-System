from datetime import timedelta
from django.db import models

from apps.core.models import AbstractBaseModel
from apps.properties.models import PropertyUnit
# Create your models here.
class Tenant(AbstractBaseModel):
    user = models.OneToOneField('users.User', on_delete=models.CASCADE)
    lease_date = models.DateField(null=True)
    move_in_date = models.DateField(null=True)
    status = models.CharField(max_length=255, default='Active')
    occupation = models.CharField(max_length=255, null=True, blank=True)
    lease_duration = models.CharField(max_length=255, null=True, blank=True)
    renews_every = models.CharField(max_length=255, null=True, blank=True)
    
    def __str__(self):
        return self.user.username
    
    def unit(self):
        return PropertyUnit.objects.filter(tenant=self).first()

    def lease_end_date(self):
        if self.lease_date:
            if self.lease_duration == '3 Months':
                return self.lease_date + timedelta(days=90)
            elif self.lease_duration == '6 Months':
                return self.lease_date + timedelta(days=180)
            elif self.lease_duration == '9 Months':
                return self.lease_date + timedelta(days=270)
            elif self.lease_duration == '1 Year':
                return self.lease_date + timedelta(days=365)
            else:
                return self.lease_date + timedelta(days=365)
        return None
    

class TenantNextOfKin(AbstractBaseModel):
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=255)
    email = models.EmailField()
    relationship = models.CharField(max_length=255)
    
    def __str__(self):
        return self.name

