from rest_framework import status, generics
from apis.subscriptions.serializers import SubscriptionSerializer
from website.models import Subscription

class SubscriptionAPIView(generics.ListCreateAPIView):
    queryset = Subscription.objects.all().order_by("created_at")
    serializer_class = SubscriptionSerializer


class SubscriptionDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Subscription.objects.all().order_by("created_at")
    serializer_class = SubscriptionSerializer

    lookup_field = "pk"
