from decimal import Decimal, InvalidOperation
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
        keyword = self.request.query_params.get('keyword', None)
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        
        filter_conditions = Q()
        if unit_type:
            unit_type = unit_type.strip()
            filter_conditions &= Q(unit_type__icontains=unit_type)
        
        if listing_type:
            listing_type = listing_type.strip()
            filter_conditions &= Q(listing_type__icontains=listing_type)
        
        if keyword:
            keyword_parts = keyword.strip().split()
            for part in keyword_parts:
                filter_conditions &= (
                    Q(property_name__icontains=part) |
                    Q(unit_description__icontains=part) |
                    Q(location_description__icontains=part) |
                    Q(unit_type__icontains=part) |
                    Q(listing_type__icontains=part) |
                    Q(city__name__icontains=part)
                )
        
        if min_price:
            try:
                min_price = Decimal(min_price)
                filter_conditions &= Q(unit_price__gte=min_price)
            except (ValueError, InvalidOperation):
                return Response({"error": "Invalid min_price value. It must be a number."}, status=status.HTTP_400_BAD_REQUEST)

        if max_price:
            try:
                max_price = Decimal(max_price)
                filter_conditions &= Q(unit_price__lte=max_price)
            except (ValueError, InvalidOperation):
                return Response({"error": "Invalid max_price value. It must be a number."}, status=status.HTTP_400_BAD_REQUEST)

        return queryset.filter(filter_conditions)
