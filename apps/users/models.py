from django.db import models
from django.contrib.auth.models import AbstractUser

from apps.core.models import AbstractBaseModel
from apps.core.constants import UserRoles
from apps.core.clean_phone_number import clean_phone_number
# Create your models here.

class User(AbstractUser, AbstractBaseModel):
    role = models.CharField(max_length=255, choices=UserRoles.choices(), default='Tenant')
    phone = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    zip_code = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    gender = models.CharField(max_length=255, blank=True, null=True)
    marital_status = models.CharField(max_length=255, blank=True, null=True)
    id_number = models.CharField(max_length=255, null=True, blank=True)
    firebase_uid = models.CharField(max_length=255, null=True, blank=True)
    profile_picture = models.URLField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.username
    
    def save(self, *args, **kwargs):
        if self.phone:
            self.phone = clean_phone_number(self.phone)
        super().save(*args, **kwargs)


    def name(self):
        return f'{self.first_name} {self.last_name}'
    
    def status(self):
        if self.is_active:
            return 'Active'
        else:
            return 'Inactive'


class HouseManager(AbstractBaseModel):
    name = models.CharField(max_length=255)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    county = models.CharField(max_length=255, blank=True, null=True)
    zip_code = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    profile_picture = models.URLField(max_length=255, null=True, blank=True)
    firebase_uid = models.CharField(max_length=255, null=True, blank=True)
    id_number = models.CharField(max_length=255, null=True, blank=True)
    gender = models.CharField(max_length=255, blank=True, null=True)
    marital_status = models.CharField(max_length=255, blank=True, null=True)
    

    def __str__(self):
        return self.name