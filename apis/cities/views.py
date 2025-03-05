from django.db.models import Q
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import AllowAny
from website.models import ListingCity, UnitListing
from apis.cities.serializers import ListingCitySerializer
from apis.listings.serializers import UnitListingSerializer


class ListingCityListView(generics.ListAPIView):
    queryset = ListingCity.objects.all()
    serializer_class = ListingCitySerializer
    permission_classes = [AllowAny]



class ListingCityDetailView(generics.RetrieveAPIView):
    queryset = ListingCity.objects.all()
    serializer_class = ListingCitySerializer
    permission_classes = [AllowAny]



class ListingCityListingsView(generics.ListAPIView):
    serializer_class = UnitListingSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = UnitListing.objects.filter(city=self.kwargs['id'])
        
        # Apply additional filters from query parameters
        unit_type = self.request.query_params.get('unit_type', None)
        listing_type = self.request.query_params.get('listing_type', None)

        filter_conditions = Q()
        if unit_type:
            unit_type = unit_type.strip()
            filter_conditions &= Q(unit_type__icontains=unit_type)
        if listing_type:
            listing_type = listing_type.strip()
            filter_conditions &= Q(listing_type__icontains=listing_type)

        return queryset.filter(filter_conditions)
