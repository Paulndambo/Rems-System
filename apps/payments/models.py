from django.db import models
from apps.core.models import AbstractBaseModel
from apps.core.constants import ExpenseTypes, PaymentMethods, PaymentStatuses
# Create your models here.
class WaterBillPayment(AbstractBaseModel):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.SET_NULL, null=True, blank=True)
    water_bill = models.ForeignKey("properties.WaterBill", on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=255, choices=PaymentMethods.choices(), null=True, blank=True)
    payment_date = models.DateField()
    month = models.ForeignKey("core.Month", on_delete=models.SET_NULL, null=True, blank=True)
    year = models.ForeignKey("core.Year", on_delete=models.SET_NULL, null=True, blank=True)

   


class Expense(AbstractBaseModel):
    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    expense_type = models.CharField(max_length=255, choices=ExpenseTypes.choices(), default=ExpenseTypes.OTHER.value)
    description = models.TextField(null=True, blank=True)
    spend_on = models.DateField()

    def __str__(self):
        return self.name
    

class RentBill(AbstractBaseModel):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.SET_NULL, null=True, blank=True, related_name="tenantrentpayments")
    unit = models.ForeignKey("properties.PropertyUnit", on_delete=models.SET_NULL, null=True, blank=True)
    amount_expected = models.DecimalField(max_digits=10, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    due_date = models.DateField()
    status = models.CharField(max_length=255, choices=PaymentStatuses.choices(), default=PaymentStatuses.PENDING.value)
    month = models.ForeignKey("core.Month", on_delete=models.SET_NULL, null=True, blank=True)
    year = models.ForeignKey("core.Year", on_delete=models.SET_NULL, null=True, blank=True)
    fully_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.tenant.user.name}"

    def balance(self):
        return self.amount_expected - self.amount_paid

class RentPayment(AbstractBaseModel):
    rent_bill = models.ForeignKey("RentBill", on_delete=models.SET_NULL, null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    payment_date = models.DateField()
    payment_method = models.CharField(max_length=255, choices=PaymentMethods.choices(), null=True, blank=True)
    

    def __str__(self):
        return f"{self.rent_bill.tenant.user.name}"


class TenantPayment(AbstractBaseModel):
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.SET_NULL, null=True, blank=True, related_name="tenantpayments")
    unit = models.ForeignKey("properties.PropertyUnit", on_delete=models.SET_NULL, null=True, blank=True)
    rent_payment = models.ForeignKey("RentPayment", on_delete=models.SET_NULL, null=True, blank=True)
    water_bill_payment = models.ForeignKey("WaterBillPayment", on_delete=models.SET_NULL, null=True, blank=True)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=255, choices=PaymentMethods.choices(), null=True, blank=True)
    payment_date = models.DateField()
    month = models.ForeignKey("core.Month", on_delete=models.SET_NULL, null=True, blank=True)
    year = models.ForeignKey("core.Year", on_delete=models.SET_NULL, null=True, blank=True)
    payment_type = models.CharField(max_length=255, null=True, blank=True)
    def __str__(self):
        return f"{self.tenant.user.name}"
