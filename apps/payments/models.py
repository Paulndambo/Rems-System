from decimal import Decimal

from django.db import models
from apps.core.models import AbstractBaseModel, WaterPrice
from apps.core.constants import MonthsNames
# Create your models here.
class WaterBill(AbstractBaseModel):
    unit = models.ForeignKey("properties.PropertyUnit", on_delete=models.CASCADE)
    month = models.CharField(max_length=255, choices=MonthsNames.choices())
    year = models.IntegerField()
    units = models.FloatField(default=0)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    
    def __str__(self):
        return f"{self.unit.name}"
    
    def save(self, *args, **kwargs):
        water_price = WaterPrice.objects.filter(is_active=True).first()
        self.amount = Decimal(self.units) * Decimal(water_price.unit_price)
        super().save(*args, **kwargs)