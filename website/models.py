from django.db import models

from apps.core.models import Month, Year, AbstractBaseModel
# Create your models here.
LISTING_TYPES_CHOICES = [
    ('Apartment', 'Apartment'),
    ('House', 'House'),
    ('AirBnB', 'AirBnB'),
    ('Room', 'Room'),
    ('Hostel', 'Hostel'),
]

LISTING_PURPOSE_CHOICES = [
    ('For Sale', 'For Sale'),
    ('For Rent', 'For Rent'),
    ('For Lease', 'For Lease'),
]

UNIT_TYPES_CHOICES = [
    ("1 Bedroom", "1 Bedroom"),
    ("2 Bedroom", "2 Bedroom"),
    ("3 Bedroom", "3 Bedroom"),
    ("4 Bedroom", "4 Bedroom"),
    ("5 Bedroom", "5 Bedroom"),
    ("Studio", "Studio"),
    ("Bedsitter", "Bedsitter"),
    ("Single Room", "Single Room"),
    ("Penthouse", "Penthouse"),
    ("Flat", "Flat"),
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

FURNISH_STATUS_CHOICES = [
    ('Fully Furnished', 'Fully Furnished'),
    ('Partially Furnished', 'Partially Furnished'),
    ('Unfurnished', 'Unfurnished'),
    ('Semi Furnished', 'Semi Furnished'),
]

NOTICE_PERIOD_CHOICES = [
    ('1 Month', '1 Month'),
    ('2 Months', '2 Months'),
    ('3 Months', '3 Months'),
    ('4 Months', '4 Months'),
    ('5 Months', '5 Months'),
]

MINIMUM_LEASE_PERIOD_CHOICES = [
    ('1 Month', '1 Month'),
    ('2 Months', '2 Months'),
    ('3 Months', '3 Months'),
    ('6 Months', '6 Months'),
    ('9 Months', '9 Months'),
    ('1 Year', '1 Year'),
    ('2 Years', '2 Years'),
    ('3 Years', '3 Years'),
    ('4 Years', '4 Years'),
    ('5 Years', '5 Years'),
]

LISTER_TYPE_CHOICES = [
    ('Internal Agent', 'Internal Agent'),
    ('External Agent', 'External Agent'),
    ('Agency', 'Agency'),
    ('Owner', 'Owner'),
]

class Subscription(AbstractBaseModel):
    name = models.CharField(max_length=255)
    cost = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=255, choices=CURRENCY_CHOICES, default='KES')
    description = models.TextField()
    is_public = models.BooleanField(default=False)


    def __str__(self):
        return self.name

class Lister(AbstractBaseModel):
    owned_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, related_name="listersowners")
    user = models.OneToOneField('users.User', on_delete=models.CASCADE)
    lister_type = models.CharField(max_length=255, choices=LISTER_TYPE_CHOICES)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    referral_code = models.CharField(max_length=255, null=True)

    def __str__(self):  
        return f"{self.user.name} - {self.lister_type}"
    
    def status(self):
        return "Active" if self.is_active else "Inactive"
    
    def listings_count(self):
        return self.listings.all().count()


class UnitListing(AbstractBaseModel):
    lister = models.ForeignKey(Lister, on_delete=models.CASCADE, related_name='listings', null=True, blank=True)
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
    unit_image_url = models.URLField(max_length=255, null=True, blank=True)
    unit_status = models.CharField(max_length=255, choices=UNIT_STATUS_CHOICES)

    minimum_lease_period = models.CharField(max_length=255, choices=MINIMUM_LEASE_PERIOD_CHOICES, default='1 Month')
    notice_period = models.CharField(max_length=255, choices=NOTICE_PERIOD_CHOICES, default='1 Month') 
    furnish_status = models.CharField(max_length=255, choices=FURNISH_STATUS_CHOICES, default='Unfurnished')

    views = models.IntegerField(default=0)
    likes = models.IntegerField(default=0)
    shares = models.IntegerField(default=0)
    comments = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=False)
    is_trending = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False) 
    owner = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True)
    town = models.CharField(max_length=255, null=True, blank=True)
    county = models.CharField(max_length=255, null=True, blank=True)
    location_description = models.TextField(null=True, blank=True)
    approved = models.BooleanField(default=False)
    commission = models.DecimalField(max_digits=100, decimal_places=2, default=0)
    contact_phone = models.CharField(max_length=255, null=True, blank=True)
    contact_name = models.CharField(max_length=255, null=True, blank=True)
    viewing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    direct_contact_fee = models.DecimalField(max_digits=10, decimal_places=2, default=100)
    def __str__(self):
        return self.property_name
     

class UnitAmenity(AbstractBaseModel):
    unit_listing = models.ForeignKey(UnitListing, on_delete=models.CASCADE, related_name='amenities')
    name = models.CharField(max_length=255)
    available = models.BooleanField(default=False)

    def __str__(self):
        return self.name   

class ListingImage(AbstractBaseModel):
    listing = models.ForeignKey(UnitListing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listing_images/')
    image_url = models.URLField(max_length=255, null=True, blank=True)
    backup_url = models.URLField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.listing.property_name

class Comment(AbstractBaseModel):
    listing = models.ForeignKey(UnitListing, on_delete=models.CASCADE)
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    comment = models.TextField()
    

class ListingInterestExpression(AbstractBaseModel):
    listing = models.ForeignKey(UnitListing, on_delete=models.CASCADE, related_name='listinginterests')
    name = models.CharField(max_length=255,null=True)
    email = models.EmailField(null=True)
    phone = models.CharField(max_length=255, null=True)
    message = models.TextField(null=True)
    processed = models.BooleanField(default=False)
    preferredContact = models.CharField(max_length=255, null=True)
    viewingDate = models.DateField(null=True)

    def __str__(self):
        return self.name


class ClientRequest(AbstractBaseModel):
    name = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    phone = models.CharField(max_length=255)
    message = models.TextField()
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    looking_to = models.CharField(max_length=255, null=True, blank=True)
    property_type = models.CharField(max_length=255, null=True, blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)
    unit_type = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return self.name

class UploadedImage(models.Model):
    image = models.ImageField(upload_to='uploads/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image uploaded at {self.uploaded_at}"