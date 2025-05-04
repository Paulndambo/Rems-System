from rest_framework import serializers
from website.models import (
    UnitListing,
    ListingImage,
    UnitAmenity,
    Comment,
    ListingInterestExpression,
    ClientRequest,
)


class ListingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage
        fields = "__all__"


class UploadListingImageSerializer(serializers.Serializer):
    listing = serializers.IntegerField()
    images = serializers.JSONField(default=list)


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:

        model = UnitAmenity
        fields = "__all__"


class UnitListingSerializer(serializers.ModelSerializer):
    location = serializers.SerializerMethodField()
    images = ListingImageSerializer(many=True, read_only=True)
    amenities = AmenitySerializer(many=True, read_only=True)

    # listing_images = serializers.JSONField(default=list, write_only=True)
    class Meta:
        model = UnitListing
        fields = "__all__"

    def get_location(self, obj):
        return f"{obj.city.name}, {obj.city.county}" if obj.city else None


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = "__all__"


class ListingInterestExpressionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingInterestExpression
        fields = "__all__"


class ClientRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClientRequest
        fields = "__all__"


class CollectListingViewsSerializer(serializers.Serializer):
    listing_id = serializers.IntegerField()
