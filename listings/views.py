from rest_framework import viewsets, filters
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Landlord, Location, VoucherType, Property, 
    PropertyImage, Amenity
)
from .serializers import (
    LandlordSerializer, LocationSerializer, VoucherTypeSerializer,
    PropertySerializer, PropertyListSerializer, PropertyImageSerializer,
    AmenitySerializer
)

class LandlordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Landlord.objects.all()
    serializer_class = LandlordSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['voucher_friendly']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']


class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['city', 'state', 'country']
    search_fields = ['city', 'state', 'address']
    ordering_fields = ['city', 'state']


class VoucherTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VoucherType.objects.all()
    serializer_class = VoucherTypeSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']


class AmenityViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Amenity.objects.all()
    serializer_class = AmenitySerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']


class PropertyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Property.objects.filter(is_available=True)
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        'property_type', 'bedrooms', 'bathrooms', 'landlord', 
        'location__city', 'location__state', 'is_featured',
        'voucher_types'
    ]
    search_fields = [
        'title', 'description', 'landlord__name', 
        'location__city', 'location__address'
    ]
    ordering_fields = [
        'rent_amount', 'date_posted', 'bedrooms', 'bathrooms'
    ]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return PropertyListSerializer
        return PropertySerializer