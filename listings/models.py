from django.db import models

class Landlord(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    voucher_friendly = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Location(models.Model):
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    
    def __str__(self):
        return f"{self.city}, {self.state}, {self.country}"

class VoucherType(models.Model):
    name = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class Amenity(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Property(models.Model):
    PROPERTY_TYPE_CHOICES = (
        ('APARTMENT', 'Apartment'),
        ('HOUSE', 'House'),
        ('CONDO', 'Condo'),
        ('TOWNHOUSE', 'Townhouse'),
    )
    SOURCE_CHOICES = (
        ('AIRBNB', 'Airbnb'),
        ('OTHER', 'Other'),
    )
    listing_id = models.CharField(max_length=50, unique=True, blank=True, null=True)  # Added for scraper
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    landlord = models.ForeignKey(Landlord, on_delete=models.SET_NULL, null=True, blank=True)
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    property_type = models.CharField(max_length=50, choices=PROPERTY_TYPE_CHOICES, default='APARTMENT')
    bedrooms = models.PositiveIntegerField(default=1)
    bathrooms = models.PositiveIntegerField(default=1)
    rent_amount = models.FloatField()
    rating = models.FloatField(blank=True, null=True)
    is_available = models.BooleanField(default=True)
    source = models.CharField(max_length=50, choices=SOURCE_CHOICES, default='AIRBNB')
    voucher_types = models.ManyToManyField(VoucherType, blank=True)
    date_posted = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_outdated = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.title} ({self.location.city}, {self.location.state})"

class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField(max_length=500)
    caption = models.CharField(max_length=255, blank=True, null=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Image for {self.property.title} (Order: {self.order})"

class PropertyAmenity(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_amenities')
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.amenity.name} for {self.property.title}"