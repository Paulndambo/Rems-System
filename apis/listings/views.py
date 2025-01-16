from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from website.models import UnitListing, ListingImage, Amenity, Comment, ListingInterestExpression
from .serializers import UnitListingSerializer, ListingImageSerializer, AmenitySerializer, CommentSerializer, ListingInterestExpressionSerializer


class UnitListingListView(generics.ListCreateAPIView):
    queryset = UnitListing.objects.all()
    serializer_class = UnitListingSerializer
    permission_classes = [AllowAny]

    
   

class UnitListingDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = UnitListing.objects.all()
    serializer_class = UnitListingSerializer
    permission_classes = [AllowAny]

    lookup_field = 'id'
