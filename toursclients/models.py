from django.db import models

from apps.core.models import AbstractBaseModel
# Create your models here.
class TourClient(AbstractBaseModel):
    name = models.CharField(max_length=255)
    gender = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255)
    id_number = models.CharField(max_length=255, null=True)
    passport_number = models.CharField(max_length=255, null=True)
    email = models.EmailField(null=True)
    dob = models.DateField()
    nationality = models.CharField(max_length=255, null=True)
    active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    def status(self):
        return "Active" if self.active else "Inactive"
    
    def full_name(self):
        return f"{self.name}"
    
    
class TourOffer(AbstractBaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField()
    image = models.ImageField(upload_to='tour_offers/', null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    per_what = models.CharField(max_length=255)
    ends_on = models.DateField()
    
    def __str__(self):
        return self.name
    

class Message(AbstractBaseModel):
    message_type = models.CharField(max_length=255, choices=(("SMS", "SMS"), ("WhatsApp", "WhatsApp"), ("Email", "Email")))
    receiver = models.ForeignKey(TourClient, on_delete=models.SET_NULL, null=True)
    purpose = models.CharField(max_length=255, choices=(("Birthday", "Birthday"), ("Holiday", "Holiday"), ("Offer", "Offer")))
    country = models.CharField(max_length=255, null=True)
    holiday_name = models.CharField(max_length=255, null=True)
    holiday_date = models.DateField(null=True)