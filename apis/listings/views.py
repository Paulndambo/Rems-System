from django.db.models import Q
from django.db import transaction

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from website.models import UnitListing, ListingImage, UnitAmenity, ClientRequest, Comment, ListingInterestExpression
from .serializers import UnitListingSerializer, ListingImageSerializer, ClientRequestSerializer, AmenitySerializer, CommentSerializer, ListingInterestExpressionSerializer, CollectListingViewsSerializer
from .filters import UnitListingFilter


class UnitListingListView(generics.ListCreateAPIView):
    queryset = UnitListing.objects.all().prefetch_related('amenities', 'images')
    serializer_class = UnitListingSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()

        # Retrieve query parameters
        town = self.request.query_params.get('town', None)
        unit_type = self.request.query_params.get('unit_type', None)
        listing_type = self.request.query_params.get('listing_type', None)

        # Dynamically build the filter
        filter_conditions = Q()
        if town:
            filter_conditions &= Q(town__icontains=town) | Q(county__icontains=town)

        if unit_type:
            filter_conditions &= Q(unit_type__icontains=unit_type)
        if listing_type:
            filter_conditions &= Q(listing_type__icontains=listing_type)

        # Apply the filter
        return queryset.filter(filter_conditions)

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        data = request.data
        serializer = self.get_serializer(data=data)
        if serializer.is_valid(raise_exception=True):
            listing = serializer.save()
            ListingImage.objects.create(listing=listing, image=data['unit_image'])
            amenities_list = ["Power Backup", "Water Backup", "Internet", "Gym", "Swimming Pool", "Kids Playground", "Security", "Parking", "Garbage Disposal", "Gas", "Laundry", "Wheelchair Access", "Elevator", "24hr Security", "24hr Water Supply", "CCTV", "Security Guard", "House Keeping", "Maintenance", "Backyard", "Balcony", "Garden", "Rooftop Access"]
            listing_amenities = []

            for amenity in amenities_list:
                listing_amenities.append(UnitAmenity(unit_listing=listing, name=amenity))
            UnitAmenity.objects.bulk_create(listing_amenities)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class UnitListingDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = UnitListing.objects.all()
    serializer_class = UnitListingSerializer
    permission_classes = [AllowAny]

    lookup_field = 'id'


class ListingImageListView(generics.ListCreateAPIView):
    queryset = ListingImage.objects.all().order_by('-created_at')
    serializer_class = ListingImageSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        queryset = super().get_queryset()
        listing_id = self.request.query_params.get('listing_id', None)
        if listing_id:
            queryset = queryset.filter(listing_id=listing_id)
        return queryset


class SubmitClientRequestAPIView(generics.CreateAPIView):
    queryset = ClientRequest.objects.all()
    serializer_class = ClientRequestSerializer


class ExpressInterestAPIView(generics.CreateAPIView):
    queryset = ListingInterestExpression.objects.all()
    serializer_class = ListingInterestExpressionSerializer


class CollectListingViewsAPIView(generics.CreateAPIView):
    serializer_class = CollectListingViewsSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid(raise_exception=True):
            listing = UnitListing.objects.filter(id=serializer.validated_data.get("listing_id")).first()
            if listing:
                listing.views += 1
                listing.save()
                return Response({ "message": "Listing views increased by 1" }, status=status.HTTP_201_CREATED)
            return Response({ "failed": "Listing views could not be increased by 1" }, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
