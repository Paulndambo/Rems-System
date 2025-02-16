import django_filters as filters
from website.models import UnitListing


class UnitListingFilter(filters.FilterSet):
    town = filters.CharFilter(field_name='town', lookup_expr='icontains')
    county = filters.CharFilter(field_name='county', lookup_expr='icontains')
    unit_type = filters.CharFilter(field_name='unit_type', lookup_expr='icontains')
    listing_type = filters.CharFilter(field_name='listing_type', lookup_expr='icontains')
    
    class Meta:
        model = UnitListing
        fields = ['town', 'county', 'unit_type', 'listing_type']