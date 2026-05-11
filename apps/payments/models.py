from django.db import models
from apps.core.models import AbstractBaseModel
from apps.core.constants import ExpenseTypes, PaymentMethods, PaymentStatuses
from decimal import Decimal
from django.urls import reverse
from django.conf import settings
from decimal import Decimal

BACKEND_BASE_URL = settings.BACKEND_BASE_URL


# Create your models here.
class UnitMonthBill(AbstractBaseModel):
    unit = models.ForeignKey("properties.PropertyUnit", on_delete=models.SET_NULL, null=True, blank=True, related_name="unitmonthbills")
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.SET_NULL, null=True, blank=True, related_name="unitmonthbills")
    month = models.ForeignKey("core.Month", on_delete=models.SET_NULL, null=True, blank=True)
    year = models.ForeignKey("core.Year", on_delete=models.SET_NULL, null=True, blank=True)
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    rent_amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    water_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    water_amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    garbage_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    garbage_amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    amount_expected = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(
        max_length=255,
        choices=PaymentStatuses.choices(),
        default=PaymentStatuses.PENDING.value,
    )
    notified = models.BooleanField(default=False)
    fully_paid = models.BooleanField(default=False)
    whatsapp_notification_sent = models.BooleanField(default=False)

    #def __str__(self):
    #    return f"{self.month.name} - {self.year.name}"

    def unit_bill_receipt_link(self):
        return f"{BACKEND_BASE_URL}/payments/unit-bill-receipt/{self.id}/"

    def update_amount_expected(self):
        self.amount_expected = (
            Decimal(self.rent_amount)
            + Decimal(self.water_amount)
        )
        self.save()

    def balance(self):
        return self.amount_expected - self.amount_paid

    def rent_balance(self):
        return self.rent_amount - self.rent_amount_paid

    def water_balance(self):
        return self.water_amount - self.water_amount_paid

    def rent_fully_paid(self):
        return self.rent_amount == self.rent_amount_paid

    def water_fully_paid(self):
        return self.water_amount == self.water_amount_paid

    def unit_bill_status(self):
        return "Fully Paid" if self.amount_expected == self.amount_paid else "Pending"

    def bill_disclaimer(self):
        message = ""
        if self.water_amount <= 0:
            message = "Water bill is missing"
    
        elif self.rent_amount <= 0:
            message = "Rent bill is missing"
        return message

    def mark_as_paid(self):
        self.status = PaymentStatuses.PAID.value
        self.fully_paid = True
        self.amount_paid = self.amount_expected
        self.water_amount_paid = self.water_amount
        self.rent_amount_paid = self.rent_amount
        self.save()


class WaterBillPayment(AbstractBaseModel):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.SET_NULL, null=True, blank=True)
    water_bill = models.ForeignKey("properties.WaterBill", on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=255, choices=PaymentMethods.choices(), null=True, blank=True)
    payment_date = models.DateField()
    month = models.ForeignKey("core.Month", on_delete=models.SET_NULL, null=True, blank=True)
    year = models.ForeignKey("core.Year", on_delete=models.SET_NULL, null=True, blank=True)


class Expense(AbstractBaseModel):
    property = models.ForeignKey("properties.Property", on_delete=models.SET_NULL, null=True, blank=True)
    unit = models.ForeignKey("properties.PropertyUnit", on_delete=models.SET_NULL, null=True, blank=True)
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    expense_type = models.CharField(max_length=255, choices=ExpenseTypes.choices(), default=ExpenseTypes.OTHER.value)
    description = models.TextField(null=True, blank=True)
    spend_on = models.DateField()

    def __str__(self):
        return self.property.name


class RentBill(AbstractBaseModel):
    unit_bill = models.ForeignKey("UnitMonthBill", on_delete=models.CASCADE, null=True, blank=True)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.SET_NULL, null=True, blank=True, related_name="tenantrentpayments")
    unit = models.ForeignKey("properties.PropertyUnit", on_delete=models.SET_NULL, null=True, blank=True)
    amount_expected = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    due_date = models.DateField()
    status = models.CharField(max_length=255, choices=PaymentStatuses.choices(), default=PaymentStatuses.PENDING.value)
    month = models.ForeignKey("core.Month", on_delete=models.SET_NULL, null=True, blank=True)
    year = models.ForeignKey("core.Year", on_delete=models.SET_NULL, null=True, blank=True)
    fully_paid = models.BooleanField(default=False)


    def balance(self):
        return self.amount_expected - self.amount_paid


class RentPayment(AbstractBaseModel):
    rent_bill = models.ForeignKey("RentBill", on_delete=models.SET_NULL, null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=255, choices=PaymentMethods.choices(), null=True, blank=True)



class GarbageBill(AbstractBaseModel):
    unit = models.ForeignKey("properties.PropertyUnit", on_delete=models.SET_NULL, null=True, blank=True, related_name="garbagebills")
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.SET_NULL, null=True, blank=True, related_name="garbagebills")
    amount_expected = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=255, choices=PaymentStatuses.choices(), default=PaymentStatuses.PENDING.value)
    fully_paid = models.BooleanField(default=False)
    month = models.ForeignKey("core.Month", on_delete=models.SET_NULL, null=True, blank=True, related_name="garbagebills")
    year = models.ForeignKey("core.Year", on_delete=models.SET_NULL, null=True, blank=True, related_name="garbagebills")


    def balance(self):
        return self.amount_expected - self.amount_paid


class GarbageBillPayment(AbstractBaseModel):
    garbage_bill = models.ForeignKey("GarbageBill", on_delete=models.SET_NULL, null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=255, choices=PaymentMethods.choices(), null=True, blank=True)



class SecurityDeposit(AbstractBaseModel):
    unit = models.ForeignKey("properties.PropertyUnit", on_delete=models.SET_NULL, null=True, blank=True)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.SET_NULL, null=True, blank=True)
    amount_expected = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=255, choices=PaymentStatuses.choices(), default=PaymentStatuses.PENDING.value)
    fully_paid = models.BooleanField(default=False)

    def __str__(self):
        return self.tenant.user.name()

    def balance(self):
        return self.amount_expected - self.amount_paid


class SecurityDepositPayment(AbstractBaseModel):
    security_deposit = models.ForeignKey("SecurityDeposit", on_delete=models.SET_NULL, null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=255, choices=PaymentMethods.choices(), null=True, blank=True)
    reference_number = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.security_deposit.tenant.user.name}"
    

class TemporaryMonthBill(AbstractBaseModel):
    unit = models.ForeignKey("properties.PropertyUnit", on_delete=models.CASCADE)
    month = models.ForeignKey("core.Month", on_delete=models.SET_NULL, null=True, blank=True)
    year = models.ForeignKey("core.Year", on_delete=models.SET_NULL, null=True, blank=True)
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    current_reading = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    previous_reading = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=255, choices=[
        ("Pending", "Pending"),
        ("Captured", "Captured"),
        ("Confirmed", "Confirmed"),
    ], default="Pending")

    def __str__(self) -> str:
        return f"{self.unit.name} - {self.month.name} {self.year.name}"
    
    def water_amount(self) -> Decimal:
        if self.current_reading > 0 :
            return round((self.current_reading - self.previous_reading) * self.unit.water_price, 2)
        return Decimal("0.00")
    
    def total(self) -> Decimal:
        return round(self.rent_amount + self.water_amount(), 2)
    

    def consumption(self) -> Decimal:
        if self.current_reading > 0:
            return self.current_reading - self.previous_reading
        return Decimal("0.00")
    


class TenantPayment(AbstractBaseModel):
    reference = models.CharField(max_length=255, null=True, blank=True)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.SET_NULL, null=True, blank=True, related_name="tenantpayments")
    unit = models.ForeignKey("properties.PropertyUnit", on_delete=models.SET_NULL, null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=255, choices=PaymentMethods.choices(), null=True, blank=True)
    payment_date = models.DateField()
    month = models.ForeignKey("core.Month", on_delete=models.SET_NULL, null=True, blank=True)
    year = models.ForeignKey("core.Year", on_delete=models.SET_NULL, null=True, blank=True)
    payment_type = models.CharField(max_length=255, choices=[
        ("General Payment", "General Payment"),
        ("Rent", "Rent"),
        ("Water Bill", "Water Bill"),
        ("Garbage Bill", "Garbage Bill"),
        ("Security Deposit", "Security Deposit"),
        ("Other", "Other"),
    ], default="Rent")
    
