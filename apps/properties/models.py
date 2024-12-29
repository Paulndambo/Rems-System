from django.db import models

from apps.core.models import AbstractBaseModel
# Create your models here.
class Property(AbstractBaseModel):
    owner = models.ForeignKey('users.User', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField()
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    units = models.PositiveIntegerField()
    #unit_rent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return self.name
    
    def total_units(self):
        return self.propertyunits.count()
    
    def occupied_units(self):
        return self.propertyunits.filter(is_occupied=True).count()
    
    def vacant_units(self):
        return self.propertyunits.filter(is_occupied=False).count()
    
    def maintenance_units(self):
        return self.propertyunits.filter(unit_type="Maintenance").count()
    
    def occupancy_rate(self):
        occupancy = (self.occupied_units() / self.total_units()) * 100 if self.total_units() > 0 else 0
        return round(occupancy, 2)
    

class PropertyUnit(AbstractBaseModel):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="propertyunits")
    name = models.CharField(max_length=255)
    rent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_occupied = models.BooleanField(default=False)
    floor = models.CharField(max_length=255, null=True, blank=True, default="1") #models.PositiveIntegerField(default=1)
    unit_type = models.CharField(max_length=255, null=True, blank=True)
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True)
    size = models.FloatField(default=0)


    def __str__(self):
        return self.name
    
    
