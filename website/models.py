from django.db import models

from apps.core.models import Month, Year, AbstractBaseModel
# Create your models here.
LISTING_TYPES_CHOICES = [
    ('Apartment', 'Apartment'),
    ('House', 'House'),
    ('AirBnB', 'AirBnB'),
    ('Room', 'Room'),
]

LISTING_PURPOSE_CHOICES = [
    ('For Sale', 'For Sale'),
    ('For Rent', 'For Rent'),
]

UNIT_TYPES_CHOICES = [
    ("1 Bedroom", "1 Bedroom"),
    ("2 Bedroom", "2 Bedroom"),
    ("3 Bedroom", "3 Bedroom"),
    ("4 Bedroom", "4 Bedroom"),
    ("5 Bedroom", "5 Bedroom"),
    ("Studio", "Studio"),
    ("Penthouse", "Penthouse"),
    ("Duplex", "Duplex"),
    ("Triplex", "Triplex"),
    ("Quadruplex", "Quadruplex"),
    ("Penthouse", "Penthouse"),
]

UNIT_STATUS_CHOICES = [
    ('Available', 'Available'),
    ('Not Available', 'Not Available'),
]

CURRENCY_CHOICES = [
    ('USD', 'USD'),
    ('NGN', 'NGN'),
    ('EUR', 'EUR'),
    ('GBP', 'GBP'),
    ('CAD', 'CAD'),
    ('ZAR', 'ZAR'),
    ('KES', 'KES'),
    ('TZS', 'TZS'),
    ('UGX', 'UGX'),
    ('RWF', 'RWF'),
    ('XOF', 'XOF'),
]

class UnitListing(AbstractBaseModel):
    property_name = models.CharField(max_length=255)
    listing_type = models.CharField(max_length=255, choices=LISTING_TYPES_CHOICES)
    listing_purpose = models.CharField(max_length=255, choices=LISTING_PURPOSE_CHOICES)
    unit_type = models.CharField(max_length=255, choices=UNIT_TYPES_CHOICES)

    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    unit_price_currency = models.CharField(max_length=255, choices=CURRENCY_CHOICES, default='KES')
    
    total_units = models.IntegerField(default=0)
    available_units = models.IntegerField(default=0)
    beds = models.IntegerField(default=0)
    baths = models.IntegerField(default=0)
    square_feet = models.IntegerField(default=0)
    pets_allowed = models.BooleanField(default=False)
    smoking_allowed = models.BooleanField(default=False)
    parking_available = models.BooleanField(default=False)
    security_available = models.BooleanField(default=False)
    security_deposit = models.DecimalField(max_digits=10, decimal_places=2)
    floor_number = models.CharField(max_length=255, null=True, blank=True)
    unit_number = models.CharField(max_length=255, null=True, blank=True)

    unit_description = models.TextField()
    unit_image = models.ImageField(upload_to='listing_images/')
    unit_status = models.CharField(max_length=255, choices=UNIT_STATUS_CHOICES)
    #unit_amenities = models.ManyToManyField('Amenity', blank=True)
    views = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False) 
    owner = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.property_name


class ListingImage(AbstractBaseModel):
    listing = models.ForeignKey(UnitListing, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='listing_images/')

    def __str__(self):
        return self.listing.unit_name


class Amenity(AbstractBaseModel):
    name = models.CharField(max_length=255)
    description = models.TextField()

    def __str__(self):
        return self.name


class Comment(AbstractBaseModel):
    listing = models.ForeignKey(UnitListing, on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ListingInterestExpression(AbstractBaseModel):
    listing = models.ForeignKey(UnitListing, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=255)
    message = models.TextField()

    def __str__(self):
        return self.title

