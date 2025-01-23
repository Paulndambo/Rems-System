from django.db import models
from django.contrib.auth.models import AbstractUser

from apps.core.models import AbstractBaseModel
from apps.core.constants import UserRoles
# Create your models here.

class User(AbstractUser, AbstractBaseModel):
    role = models.CharField(max_length=255, choices=UserRoles.choices(), default='Landlord')
    phone = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    zip_code = models.CharField(max_length=255, blank=True, null=True)
    country = models.CharField(max_length=255, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    gender = models.CharField(max_length=255, blank=True, null=True)
    id_number = models.CharField(max_length=255, null=True, blank=True)
    firebase_uid = models.CharField(max_length=255, null=True, blank=True)
    profile_picture = models.URLField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.username

    def name(self):
        return f'{self.first_name} {self.last_name}'
