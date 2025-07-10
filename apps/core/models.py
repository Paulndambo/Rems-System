from django.db import models


# Create your models here.
class AbstractBaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        abstract = True


class WaterPrice(AbstractBaseModel):
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Ksh {self.unit_price}"


class Year(AbstractBaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"


class Month(AbstractBaseModel):
    name = models.CharField(max_length=255)
    year = models.ForeignKey(Year, on_delete=models.CASCADE, related_name="months")

    def __str__(self):
        return f"{self.name}"


class UserAction(AbstractBaseModel):
    action_type = models.CharField(max_length=255)
    user = models.ForeignKey(
        "users.User", on_delete=models.CASCADE, related_name="user_actions"
    )
    action_details = models.TextField(null=True, blank=True)

    def __str__(self):
        return f"{self.action_type}"