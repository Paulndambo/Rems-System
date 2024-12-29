from decimal import Decimal

from django.db import models
from apps.core.models import AbstractBaseModel, WaterPrice
from apps.core.constants import MonthsNames, PaymentStatuses
# Create your models here.
class WaterBill(AbstractBaseModel):
    unit = models.ForeignKey("properties.PropertyUnit", on_delete=models.CASCADE)
    month = models.CharField(max_length=255, choices=MonthsNames.choices())
    year = models.IntegerField()
    units = models.FloatField(default=0)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.SET_NULL, null=True, blank=True, related_name="waterbills")
    
    
    def __str__(self):
        return f"{self.unit.name}"
    
    def save(self, *args, **kwargs):
        water_price = WaterPrice.objects.filter(is_active=True).first()
        self.amount = Decimal(self.units) * Decimal(water_price.unit_price)
        super().save(*args, **kwargs)

class RentBill(AbstractBaseModel):
    unit = models.ForeignKey("properties.PropertyUnit", on_delete=models.CASCADE)
    month = models.CharField(max_length=255, choices=MonthsNames.choices())
    year = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.SET_NULL, null=True, blank=True, related_name="rentbills")
    status = models.CharField(max_length=255, default=PaymentStatuses.FUTURE.value, choices=PaymentStatuses.choices())

    def __str__(self):
        return f"{self.unit.name}"

class TenantPayment(AbstractBaseModel):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.CASCADE)
    water_bill = models.ForeignKey("payments.WaterBill", on_delete=models.SET_NULL, null=True, blank=True)
    rent_bill = models.ForeignKey("payments.RentBill", on_delete=models.SET_NULL, null=True, blank=True)
    previous_balances = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    water_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_expected = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    date_expected = models.DateField()
    date_paid = models.DateField(null=True, blank=True)
    month = models.CharField(max_length=255, choices=MonthsNames.choices())
    year = models.CharField(max_length=255)
    reference = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, default=PaymentStatuses.FUTURE.value, choices=PaymentStatuses.choices())
    
    def save(self, *args, **kwargs):
        self.amount_expected = self.rent_amount + self.water_amount + self.previous_balances
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.tenant.user.name}"