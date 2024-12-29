from django.db import models

# Create your models here.
class AbstractBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    

    class Meta:
        abstract = True


class WaterPrice(AbstractBaseModel):
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    
    
    def __str__(self):
        return f"Ksh {self.unit_price}"