from django.db import models
from django.utils import timezone


class Landlord(models.Model):
    """Model representing property landlords/owners/companies"""
    name = models.CharField(max_length=255)
    website = models.URLField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    logo_url = models.URLField(blank=True, null=True)
    voucher_friendly = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class Location(models.Model):
    """Model representing property locations"""
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100, default='United States')
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.city}, {self.state}"
    
    class Meta:
        ordering = ['city', 'state']


class VoucherType(models.Model):
    """Model representing different types of housing vouchers accepted"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class Property(models.Model):
    """Model representing property listings"""
    PROPERTY_TYPES = [
        ('apartment', 'Apartment'),
        ('house', 'House'),
        ('condo', 'Condominium'),
        ('townhouse', 'Townhouse'),
        ('duplex', 'Duplex'),
        ('studio', 'Studio'),
        ('other', 'Other'),
    ]
    
    SOURCE_CHOICES = [
        ('zillow', 'Zillow'),
        ('apartments', 'Apartments.com'),
        ('realtor', 'Realtor.com'),
        ('craigslist', 'Craigslist'),
        ('housing_authority', 'Housing Authority'),
        ('manual', 'Manually Added'),
        ('other', 'Other Source'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    property_type = models.CharField(max_length=20, choices=PROPERTY_TYPES, default='apartment')
    bedrooms = models.IntegerField(default=1)
    bathrooms = models.DecimalField(max_digits=3, decimal_places=1, default=1.0)
    square_feet = models.IntegerField(blank=True, null=True)
    
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2)
    deposit_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    landlord = models.ForeignKey(Landlord, on_delete=models.CASCADE, related_name='properties')
    location = models.ForeignKey(Location, on_delete=models.CASCADE, related_name='properties')
    voucher_types = models.ManyToManyField(VoucherType, related_name='properties')
    
    is_available = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    date_posted = models.DateTimeField(default=timezone.now)
    date_available = models.DateField(blank=True, null=True)
    
    # Listing source tracking
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='manual')
    external_id = models.CharField(max_length=100, blank=True, null=True)
    external_url = models.URLField(blank=True, null=True)
    last_scraped = models.DateTimeField(blank=True, null=True)
    
    # Images
    main_image_url = models.URLField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} - {self.location.city}, {self.location.state}"
    
    class Meta:
        verbose_name_plural = "Properties"
        ordering = ['-date_posted']


class PropertyImage(models.Model):
    """Model for property images"""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='images')
    image_url = models.URLField()
    caption = models.CharField(max_length=255, blank=True, null=True)
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.property}"
    
    class Meta:
        ordering = ['order']


class Amenity(models.Model):
    """Model for property amenities"""
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Amenities"


class PropertyAmenity(models.Model):
    """Junction model for property amenities"""
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name='property_amenities')
    amenity = models.ForeignKey(Amenity, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.amenity.name} at {self.property}"
    
    class Meta:
        verbose_name_plural = "Property Amenities"