from rest_framework import serializers
from website.models import ListingCity


class ListingCitySerializer(serializers.ModelSerializer):
    listings = serializers.SerializerMethodField()

    class Meta:
        model = ListingCity
        fields = "__all__"

    def get_listings(self, obj):
        return obj.listingsincity.count()
