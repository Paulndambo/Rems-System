from django.urls import path
from apps.notifications.views import send_unit_bill_notification

urlpatterns = [
    path(
        "send-unit-bill-notification/",
        send_unit_bill_notification,
        name="send-unit-bill-notification",
    ),
]
