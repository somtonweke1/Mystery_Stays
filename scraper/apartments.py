import re
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from django.utils import timezone
from .base import BaseScraper

logger = logging.getLogger(__name__)

class ApartmentsDotComScraper(BaseScraper):
    """Scraper for Apartments.com rental listings"""
    
    BASE_URL = "https://www.apartments.com/"
    
    def scrape_listings(self, location="", voucher_keywords=None, max_pages=1):
        """
        Scrape Apartments.com for voucher-accepting properties
        
        Args:
            location: City or ZIP code to search
            voucher_keywords: List of keywords to search for voucher acceptance
            max_pages: Maximum number of pages to scrape
        
        Returns:
            List of saved property objects
        """
        if voucher_keywords is None:
            voucher_keywords = ["section 8", "housing voucher", "voucher accepted", "vouchers welcome"]
        
        properties = []
        search_url = f"{self.BASE_URL}{location.replace(' ', '-')}/"
        
        for page in range(1, max_pages + 1):
            if page > 1:
                page_url = f"{search_url}{page}/"
            else:
                page_url = search_url
                
            logger.info(f"Scraping Apartments.com page {page}: {page_url}")
            html = self.get_page(page_url)
            
            if not html:
                logger.warning(f"Failed to fetch page {page}")
                break
                
            # Parse the page
            soup = BeautifulSoup(html, 'html.parser')
            
            # Find all property listings
            property_cards = soup.find_all('article', class_='placard')
            
            for card in property_cards:
                # Get the detail URL
                link = card.find('a', class_='property-link')
                if not link or not link.get('href'):
                    continue
                    
                detail_url = link['href']
                detail_html = self.get_page(detail_url)
                
                if not detail_html:
                    continue
                    
                detail_soup = BeautifulSoup(detail_html, 'html.parser')
                
                # Check if the property accepts housing vouchers
                policy_section = detail_soup.find('div', id='policySection')
                description = detail_soup.find('section', id='descriptionSection')
                
                accepts_vouchers = False
                
                # Check in policy section
                if policy_section:
                    policy_text = policy_section.text.lower()
                    accepts_vouchers = any(keyword.lower() in policy_text for keyword in voucher_keywords)
                
                # Check in description
                if not accepts_vouchers and description:
                    desc_text = description.text.lower()
                    accepts_vouchers = any(keyword.lower() in desc_text for keyword in voucher_keywords)
                
                if accepts_vouchers:
                    # Extract property data
                    property_data = self.extract_property_data(card, detail_soup, detail_url)
                    saved_property = self.save_listing(property_data, 'apartments')
                    properties.append(saved_property)
            
        return properties
    
    def extract_property_data(self, card, detail_soup, detail_url):
        """
        Extract structured data from an Apartments.com listing
        
        Args:
            card: BeautifulSoup object for the property card
            detail_soup: BeautifulSoup object for the detail page
            detail_url: URL of the detail page
        
        Returns:
            Dict with structured property data
        """
        # Initialize data with defaults
        data = {
            'external_url': detail_url,
            'last_scraped': timezone.now(),
            'source': 'apartments'
        }
        
        # Extract data from the card
        property_title = card.find('span', class_='property-title')
        if property_title:
            data['title'] = property_title.text.strip()
        
        property_address = card.find('div', class_='property-address')
        if property_address:
            data['address'] = property_address.text.strip()
        
        # External ID from URL
        id_match = re.search(r'/(\d+)/', detail_url)
        if id_match:
            data['external_id'] = id_match.group(1)
        
        # Extract more details from the detail page
        if detail_soup:
            # Pricing
            price_elem = detail_soup.find('span', class_='rentPrice')
            if price_elem:
                price_text = price_elem.text.strip()
                price_match = re.search(r'[\$]?([0-9,]+)', price_text)
                if price_match:
                    data['rent_amount'] = float(price_match.group(1).replace(',', ''))
            
            # Location details
            address_elem = detail_soup.find('div', class_='propertyAddress')
            if address_elem:
                city_state_zip = address_elem.find('span', class_='stateZipContainer')
                if city_state_zip:
                    # Parse city, state, zip
                    csz_text = city_state_zip.text.strip()
                    csz_match = re.match(r'([^,]+),\s*([A-Z]{2})\s*(\d{5})', csz_text)
                    if csz_match:
                        data['city'] = csz_match.group(1)
                        data['state'] = csz_match.group(2)
                        data['zip_code'] = csz_match.group(3)
            
            # Landlord info
            company_elem = detail_soup.find('div', class_='companyName')
            if company_elem:
                data['landlord_name'] = company_elem.text.strip()
            else:
                data['landlord_name'] = "Property Manager"
            
            # Description
            description_elem = detail_soup.find('section', id='descriptionSection')
            if description_elem:
                desc_content = description_elem.find('p')
                if desc_content:
                    data['description'] = desc_content.text.strip()
            
            # Property details (bedrooms, bathrooms, sqft)
            details_elems = detail_soup.find_all('span', class_='detailsTextWrapper')
            for detail in details_elems:
                detail_text = detail.text.lower()
                
                # Bedrooms
                if 'bed' in detail_text:
                    bed_match = re.search(r'(\d+)\s*bed', detail_text)
                    if bed_match:
                        data['bedrooms'] = int(bed_match.group(1))
                    elif 'studio' in detail_text:
                        data['bedrooms'] = 0
                        data['property_type'] = 'studio'
                
                # Bathrooms
                if 'bath' in detail_text:
                    bath_match = re.search(r'(\d+(?:\.\d+)?)\s*bath', detail_text)
                    if bath_match:
                        data['bathrooms'] = float(bath_match.group(1))
                
                # Square feet
                if 'sq ft' in detail_text:
                    sqft_match = re.search(r'(\d+(?:,\d+)?)\s*sq ft', detail_text)
                    if sqft_match:
                        data['square_feet'] = int(sqft_match.group(1).replace(',', ''))
            
            # Property type
            property_type_elems = detail_soup.find_all('span', class_='propertyType')
            for elem in property_type_elems:
                type_text = elem.text.lower()
                if 'apartment' in type_text:
                    data['property_type'] = 'apartment'
                elif 'house' in type_text:
                    data['property_type'] = 'house'
                elif 'condo' in type_text:
                    data['property_type'] = 'condo'
                elif 'townhouse' in type_text:
                    data['property_type'] = 'townhouse'
                elif 'duplex' in type_text:
                    data['property_type'] = 'duplex'
            
            # If property type is still not set, default to apartment
            if 'property_type' not in data:
                data['property_type'] = 'apartment'
            
            # Available date (often not explicitly stated, use a default of 1 month from now)
            data['date_available'] = (datetime.now() + timedelta(days=30)).date()
            
            # Images
            images = []
            carousel = detail_soup.find('div', class_='carouselContent')
            if carousel:
                img_tags = carousel.find_all('img')
                for img in img_tags:
                    if img.get('src') and img.get('src').startswith('http'):
                        images.append(img.get('src'))
            
            if images:
                data['images'] = images
                if images[0]:
                    data['main_image_url'] = images[0]
            
            # Amenities
            amenities = []
            amenities_section = detail_soup.find('div', id='amenitiesSection')
            if amenities_section:
                amenity_items = amenities_section.find_all('li')
                for item in amenity_items:
                    amenities.append(item.text.strip())
            
            if amenities:
                data['amenities'] = amenities
                
            # Voucher types - set Section 8 as default for voucher-friendly properties
            data['voucher_types'] = ['Section 8']
            
            # Deposit amount (if available)
            deposit_elem = detail_soup.find('div', string=re.compile('Deposit'))
            if deposit_elem:
                deposit_match = re.search(r'[\$]?([0-9,]+)', deposit_elem.text)
                if deposit_match:
                    data['deposit_amount'] = float(deposit_match.group(1).replace(',', ''))
        
        return data