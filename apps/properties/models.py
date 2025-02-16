from decimal import Decimal
from django.db import models


from apps.core.models import AbstractBaseModel, WaterPrice
from apps.core.constants import MaintenanceStatuses, PriorityLevels

# Create your models here.
class Property(AbstractBaseModel):
    owner = models.ForeignKey('users.User', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    units = models.PositiveIntegerField()
    house_manager = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name="managedproperties")
    garbage_charge = models.DecimalField(max_digits=10, decimal_places=2, default=130.00)


    def __str__(self):
        return self.name

    def status(self):
        return "Active" if self.is_active else "Inactive"
    
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
    
    def monthly_revenue(self):
        return sum(list(self.propertyunits.filter(is_occupied=True).values_list('rent', flat=True)))
    

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
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    water_meter_number = models.CharField(max_length=255, null=True, blank=True)
    electricity_meter_number = models.CharField(max_length=255, null=True, blank=True)
    water_price = models.DecimalField(max_digits=10, decimal_places=2, default=200.00)

    def __str__(self):
        return self.name
    
    
class MaintenanceRequest(AbstractBaseModel):
    title = models.CharField(max_length=255)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    unit = models.ForeignKey(PropertyUnit, on_delete=models.CASCADE)
    priority = models.CharField(max_length=255, choices=PriorityLevels.choices(), default=PriorityLevels.MEDIUM.value)
    description = models.TextField()
    status = models.CharField(max_length=255, default=MaintenanceStatuses.PENDING.value, choices=MaintenanceStatuses.choices())
    image = models.ImageField(upload_to='maintenance/', blank=True, null=True)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    def __str__(self):
        return self.name
    

class WaterBill(AbstractBaseModel):
    unit_bill = models.ForeignKey("payments.UnitMonthBill", on_delete=models.CASCADE, null=True, blank=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    unit = models.ForeignKey(PropertyUnit, on_delete=models.CASCADE, related_name="unitwaterbills")
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.SET_NULL, null=True, blank=True, related_name="tenantwaterbills")
    reading_date = models.DateField(null=True, blank=True)
    month = models.ForeignKey("core.Month", on_delete=models.SET_NULL, null=True, blank=True)
    year = models.ForeignKey("core.Year", on_delete=models.SET_NULL, null=True, blank=True)
    meter_number = models.CharField(max_length=255, null=True, blank=True)
    previous_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    previous_reading = models.DecimalField(max_digits=10, decimal_places=4, default=0.00)
    current_reading = models.DecimalField(max_digits=10, decimal_places=4, default=0.00)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=255, default=MaintenanceStatuses.PENDING.value, choices=MaintenanceStatuses.choices())
    due_date = models.DateField(null=True, blank=True)
    fully_paid = models.BooleanField(default=False)

    def __str__(self):
        return self.unit.name
    

    def total_amount(self):
        water_price = self.unit.water_price
        return (Decimal(water_price) * Decimal(self.current_reading)) + Decimal(self.previous_balance)

    def save(self, *args, **kwargs):
        
        if not self.tenant and self.unit:
            self.tenant = self.unit.tenant
        self.amount = self.total_amount()
        super().save(*args, **kwargs)

    def balance(self):
        return self.amount - self.amount_paid


class GarbageBill(AbstractBaseModel):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    unit = models.ForeignKey(PropertyUnit, on_delete=models.CASCADE, related_name="unitgarbagebills")
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.SET_NULL, null=True, blank=True, related_name="tenantgarbagebills")
    month = models.ForeignKey("core.Month", on_delete=models.SET_NULL, null=True, blank=True)
    year = models.ForeignKey("core.Year", on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=255, default=MaintenanceStatuses.PENDING.value, choices=MaintenanceStatuses.choices())

    def __str__(self):
        return self.unit.name
    

class ElectricityBill(AbstractBaseModel):
    property = models.ForeignKey(Property, on_delete=models.CASCADE)
    unit = models.ForeignKey(PropertyUnit, on_delete=models.CASCADE, related_name="unitelectricitybills")
    tenant = models.ForeignKey('tenants.Tenant', on_delete=models.SET_NULL, null=True, blank=True, related_name="tenantelectricitybills")
    month = models.ForeignKey("core.Month", on_delete=models.SET_NULL, null=True, blank=True)
    year = models.ForeignKey("core.Year", on_delete=models.SET_NULL, null=True, blank=True)
    meter_number = models.CharField(max_length=255, null=True, blank=True)
    previous_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    previous_reading = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    current_reading = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    status = models.CharField(max_length=255, default=MaintenanceStatuses.PENDING.value, choices=MaintenanceStatuses.choices())

    def __str__(self):
        return self.unit.name
    

    
    def balance(self):
        return self.amount - self.amount_paid