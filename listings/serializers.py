from rest_framework import serializers
from .models import (
    Landlord, Location, VoucherType, Property, 
    PropertyImage, Amenity, PropertyAmenity
)

class LandlordSerializer(serializers.ModelSerializer):
    class Meta:
        model = Landlord
        fields = '__all__'


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'


class VoucherTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = VoucherType
        fields = '__all__'


class AmenitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Amenity
        fields = '__all__'


class PropertyImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyImage
        fields = ['id', 'image_url', 'caption', 'order']


class PropertySerializer(serializers.ModelSerializer):
    landlord = LandlordSerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    voucher_types = VoucherTypeSerializer(many=True, read_only=True)
    images = PropertyImageSerializer(many=True, read_only=True)
    
    # Add amenities 
    amenities = serializers.SerializerMethodField()
    
    def get_amenities(self, obj):
        property_amenities = PropertyAmenity.objects.filter(property=obj)
        return [pa.amenity.name for pa in property_amenities]
    
    class Meta:
        model = Property
        fields = [
            'id', 'title', 'description', 'property_type', 'bedrooms', 
            'bathrooms', 'square_feet', 'rent_amount', 'deposit_amount',
            'landlord', 'location', 'voucher_types', 'is_available',
            'date_posted', 'date_available', 'source', 'external_url',
            'main_image_url', 'images', 'amenities',
        ]


class PropertyListSerializer(serializers.ModelSerializer):
    """Simplified property serializer for list views"""
    landlord_name = serializers.CharField(source='landlord.name')
    location_str = serializers.SerializerMethodField()
    
    def get_location_str(self, obj):
        return f"{obj.location.city}, {obj.location.state}"
    
    class Meta:
        model = Property
        fields = [
            'id', 'title', 'property_type', 'bedrooms', 'bathrooms', 
            'rent_amount', 'landlord_name', 'location_str', 'is_available',
            'date_posted', 'main_image_url'
        ]