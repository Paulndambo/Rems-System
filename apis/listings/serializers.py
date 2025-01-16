from rest_framework import serializers
from website.models import UnitListing, ListingImage, Amenity, Comment, ListingInterestExpression

class UnitListingSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitListing
        fields = '__all__'


class ListingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingImage
        fields = '__all__'

class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = '__all__'


class ListingInterestExpressionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ListingInterestExpression
        fields = '__all__'

