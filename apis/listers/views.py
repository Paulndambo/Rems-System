from rest_framework import status, generics
from apis.listers.serializers import ListerSerializer
from website.models import Lister


class ListerAPIView(generics.ListCreateAPIView):
    queryset = Lister.objects.all().order_by("created_at")
    serializer_class = ListerSerializer


class ListerDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Lister.objects.all().order_by("created_at")
    serializer_class = ListerSerializer

    lookup_field = "pk"
