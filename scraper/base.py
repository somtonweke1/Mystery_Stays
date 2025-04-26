import time
import logging
from abc import ABC, abstractmethod
from django.conf import settings
import requests

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Base class for all property listing scrapers"""
    
    def __init__(self):
        self.headers = {
            'User-Agent': settings.SCRAPER_USER_AGENT,
            'Accept-Language': 'en-US,en;q=0.9',
        }
        self.delay = settings.SCRAPER_REQUEST_DELAY

    @abstractmethod
    def scrape_listings(self, **kwargs):
        """Scrape property listings from the source"""
        pass
    
    @abstractmethod
    def extract_property_data(self, listing_data):
        """Extract structured data from a listing"""
        pass
    
    def get_page(self, url):
        """Make a GET request with error handling and rate limiting"""
        try:
            # Rate limiting
            time.sleep(self.delay)
            
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logger.error(f"Error fetching {url}: {str(e)}")
            return None
    
    def save_listing(self, listing_data, source):
        """Save listing data to database"""
        from listings.models import Property, Landlord, Location, VoucherType
        
        # Skip if we already have this listing (based on external_id)
        if listing_data.get('external_id'):
            existing = Property.objects.filter(
                external_id=listing_data['external_id'],
                source=source
            ).first()
            if existing:
                # Update last_scraped timestamp
                existing.last_scraped = listing_data.get('last_scraped')
                existing.save(update_fields=['last_scraped'])
                return existing
        
        # Get or create landlord
        landlord, _ = Landlord.objects.get_or_create(
            name=listing_data['landlord_name'],
            defaults={
                'website': listing_data.get('landlord_website'),
                'phone': listing_data.get('landlord_phone'),
                'email': listing_data.get('landlord_email'),
                'voucher_friendly': True  # Assume true since we're scraping voucher-friendly properties
            }
        )
        
        # Get or create location
        location, _ = Location.objects.get_or_create(
            city=listing_data['city'],
            state=listing_data['state'],
            defaults={
                'zip_code': listing_data.get('zip_code'),
                'address': listing_data.get('address'),
                'country': listing_data.get('country', 'United States')
            }
        )
        
        # Create the property
        property_obj = Property.objects.create(
            title=listing_data['title'],
            description=listing_data.get('description', ''),
            property_type=listing_data.get('property_type', 'apartment'),
            bedrooms=listing_data.get('bedrooms', 1),
            bathrooms=listing_data.get('bathrooms', 1),
            square_feet=listing_data.get('square_feet'),
            rent_amount=listing_data['rent_amount'],
            deposit_amount=listing_data.get('deposit_amount'),
            landlord=landlord,
            location=location,
            is_available=True,
            is_featured=listing_data.get('is_featured', False),
            date_posted=listing_data.get('date_posted'),
            date_available=listing_data.get('date_available'),
            source=source,
            external_id=listing_data.get('external_id'),
            external_url=listing_data.get('external_url'),
            last_scraped=listing_data.get('last_scraped'),
            main_image_url=listing_data.get('main_image_url')
        )
        
        # Add voucher types
        for voucher_name in listing_data.get('voucher_types', []):
            voucher, _ = VoucherType.objects.get_or_create(name=voucher_name)
            property_obj.voucher_types.add(voucher)
        
        # Add images
        if listing_data.get('images'):
            from listings.models import PropertyImage
            for i, img_url in enumerate(listing_data['images']):
                PropertyImage.objects.create(
                    property=property_obj,
                    image_url=img_url,
                    order=i
                )
        
        # Add amenities
        if listing_data.get('amenities'):
            from listings.models import Amenity, PropertyAmenity
            for amenity_name in listing_data['amenities']:
                amenity, _ = Amenity.objects.get_or_create(name=amenity_name)
                PropertyAmenity.objects.create(
                    property=property_obj,
                    amenity=amenity
                )
        
        return property_obj