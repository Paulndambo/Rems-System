from rest_framework import serializers
from website.models import Lister


class ListerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lister
        fields = "__all__"
