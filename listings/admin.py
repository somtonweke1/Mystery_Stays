from django.contrib import admin
from .models import (
    Landlord, Location, VoucherType, Property, 
    PropertyImage, Amenity, PropertyAmenity
)

@admin.register(Landlord)
class LandlordAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'phone', 'voucher_friendly', 'created_at')
    list_filter = ('voucher_friendly',)
    search_fields = ('name', 'email', 'phone')


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('city', 'state', 'country', 'zip_code')
    list_filter = ('state', 'country')
    search_fields = ('city', 'state', 'zip_code', 'address')


@admin.register(VoucherType)
class VoucherTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)


class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    extra = 1


class PropertyAmenityInline(admin.TabularInline):
    model = PropertyAmenity
    extra = 1


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = ('title', 'landlord', 'get_location', 'property_type', 
                    'bedrooms', 'bathrooms', 'rent_amount', 'is_available', 
                    'source', 'date_posted')
    list_filter = ('is_available', 'property_type', 'source', 'location__city', 
                   'location__state', 'landlord')
    search_fields = ('title', 'description', 'landlord__name', 
                     'location__city', 'location__state', 'location__address')
    filter_horizontal = ('voucher_types',)
    inlines = [PropertyImageInline, PropertyAmenityInline]
    date_hierarchy = 'date_posted'
    
    def get_location(self, obj):
        return f"{obj.location.city}, {obj.location.state}"
    get_location.short_description = 'Location'


@admin.register(PropertyImage)
class PropertyImageAdmin(admin.ModelAdmin):
    list_display = ('property', 'image_url', 'order', 'created_at')
    list_filter = ('property__landlord',)
    search_fields = ('property__title', 'caption')


@admin.register(Amenity)
class AmenityAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)