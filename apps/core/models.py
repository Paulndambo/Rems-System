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
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="actions")
    action = models.CharField(max_length=255)
    action_type = models.CharField(max_length=255, default="Created")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.action}"