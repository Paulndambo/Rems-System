import os
import time

from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage

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
from .serializers import UnitListingSerializer, ListingImageSerializer, ClientRequestSerializer, AmenitySerializer, CommentSerializer, ListingInterestExpressionSerializer, CollectListingViewsSerializer, UploadListingImageSerializer
from .filters import UnitListingFilter
from apps.core.cloudinary_handler import CloudinaryHandler
from apps.core.firebase_files_handler import FirebaseFilesHandler

fs = FileSystemStorage(location='temp')

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
            town = town.strip()
            filter_conditions &= Q(town__icontains=town) | Q(county__icontains=town)

        if unit_type:
            unit_type = unit_type.strip()
            filter_conditions &= Q(unit_type__icontains=unit_type)
        if listing_type:
            listing_type = listing_type.strip()
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

    @transaction.atomic
    def post(self, request, *args, **kwargs):

        data = request.data
        serializer = self.serializer_class(data=data)


        if serializer.is_valid(raise_exception=True):
            try:
                image_file = serializer.validated_data['image']

                file_extension = image_file.name.split('.')[-1].lower()
                file_content = image_file.read()
                file_content = ContentFile(file_content)
                file_name = fs.save(
                    f"temp_source_file.{file_extension}", file_content
                )
                temp_file = fs.path(file_name)

                cloudinary_handler = CloudinaryHandler()
                upload_result = cloudinary_handler.upload_image(temp_file, 'listing_images')

                listing_image = serializer.save()
                listing_image.image_url = upload_result['public_url']
                listing_image.save()    

                cloudinary_handler.clean_up_temp_file(temp_file)
                return Response({"data": serializer.data, "upload_result": upload_result}, status=status.HTTP_201_CREATED)
            except Exception as e:
                cloudinary_handler.clean_up_temp_file(temp_file)
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UploadListingImageAPIView(generics.ListCreateAPIView):
    serializer_class = UploadListingImageSerializer
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        print(request.data)
        if serializer.is_valid(raise_exception=True):

            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ClientRequestsAPIView(generics.ListCreateAPIView):
    queryset = ClientRequest.objects.all()
    serializer_class = ClientRequestSerializer

    def get_permissions(self):
        if self.request.method in ['GET', 'DELETE', 'PUT', 'PATCH']:
            return [IsAuthenticated()]
        return [AllowAny()]


class ClientRequestDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ClientRequest.objects.all()
    serializer_class = ClientRequestSerializer
    
    lookup_field = 'id'


class PropertyViewInterestsAPIView(generics.ListCreateAPIView):
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
