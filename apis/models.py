from enum import Enum
from django.db import models
from apps.core.models import AbstractBaseModel
from website.models import UnitListing


# Create your models here.
class RequestType(Enum):
    LANDLORD_DETAILS = "Landlord Details"
    SUBSCRIPTION = "Subscription"
    PAYMENT = "Payment"

    @classmethod
    def choices(cls):
        return [(choice.value, choice.name) for choice in cls]


class PreferredContact(Enum):
    EMAIL = "Email"
    PHONE = "Phone"
    WHATSAPP = "Whatsapp"
    SMS = "SMS"

    @classmethod
    def choices(cls):
        return [(choice.value, choice.name) for choice in cls]


class PaymentStatus(Enum):
    PAID = "Paid"
    PENDING = "Pending"
    FAILED = "Failed"

    @classmethod
    def choices(cls):
        return [(choice.value, choice.name) for choice in cls]


class Customer(AbstractBaseModel):
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class PaymentRecord(AbstractBaseModel):
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, null=True, blank=True)
    payment_channel = models.CharField(max_length=255, null=True, blank=True)
    bank = models.CharField(max_length=255, null=True, blank=True)
    country_code = models.CharField(max_length=255, null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    reference = models.CharField(max_length=255, null=True, blank=True)
    payment_status = models.CharField(
        max_length=255, null=True, blank=True, choices=PaymentStatus.choices()
    )

    listing = models.ForeignKey(
        UnitListing, on_delete=models.CASCADE, null=True, blank=True
    )
    request_type = models.CharField(
        max_length=255, null=True, blank=True, choices=RequestType.choices()
    )
    preferred_contact = models.CharField(
        max_length=255, null=True, blank=True, choices=PreferredContact.choices()
    )

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.reference} - {self.amount}"
