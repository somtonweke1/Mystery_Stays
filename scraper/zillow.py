import json
import re
import logging
from datetime import datetime
from bs4 import BeautifulSoup
from django.utils import timezone
from .base import BaseScraper

logger = logging.getLogger(__name__)

class ZillowScraper(BaseScraper):
    """Scraper for Zillow rental listings"""
    
    BASE_URL = "https://www.zillow.com/homes/for_rent/"
    
    def scrape_listings(self, location="", voucher_keywords=None, max_pages=1):
        """
        Scrape Zillow for voucher-accepting properties
        
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
        search_url = f"{self.BASE_URL}{location.replace(' ', '-')}_rb/"
        
        for page in range(1, max_pages + 1):
            if page > 1:
                page_url = f"{search_url}{page}_p/"
            else:
                page_url = search_url
                
            logger.info(f"Scraping Zillow page {page}: {page_url}")
            html = self.get_page(page_url)
            
            if not html:
                logger.warning(f"Failed to fetch page {page}")
                break
                
            # Parse the page
            soup = BeautifulSoup(html, 'html.parser')
            
            # Zillow has its listing data in a script tag as JSON
            script_tags = soup.find_all('script', type='application/json')
            listing_data = None
            
            for script in script_tags:
                if script.text and 'queryState' in script.text:
                    try:
                        data = json.loads(script.text)
                        if 'cat1' in data and 'searchResults' in data['cat1']:
                            listing_data = data['cat1']['searchResults']['listResults']
                            break
                    except (json.JSONDecodeError, KeyError) as e:
                        continue
            
            if not listing_data:
                logger.warning("Could not find listing data on page")
                continue
                
            # Process each listing
            for listing in listing_data:
                # Check for voucher keywords in the description
                detail_url = f"https://www.zillow.com{listing.get('detailUrl')}"
                detail_html = self.get_page(detail_url)
                
                if not detail_html:
                    continue
                    
                detail_soup = BeautifulSoup(detail_html, 'html.parser')
                description = detail_soup.find('div', {'data-testid': 'description'})
                
                if not description:
                    continue
                    
                description_text = description.text.lower()
                
                # Check if any voucher keyword is in the description
                accepts_vouchers = any(keyword.lower() in description_text for keyword in voucher_keywords)
                
                if accepts_vouchers:
                    property_data = self.extract_property_data(listing, detail_soup)
                    saved_property = self.save_listing(property_data, 'zillow')
                    properties.append(saved_property)
            
        return properties
    
    def extract_property_data(self, listing, detail_soup=None):
        """
        Extract structured data from a Zillow listing
        
        Args:
            listing: JSON listing data from Zillow
            detail_soup: BeautifulSoup object for the listing detail page
        
        Returns:
            Dict with structured property data
        """
        # Basic listing info
        data = {
            'title': listing.get('statusText', '') + ' ' + listing.get('address', ''),
            'external_id': str(listing.get('id')),
            'external_url': f"https://www.zillow.com{listing.get('detailUrl')}",
            'rent_amount': float(listing.get('price', '').replace('$', '').replace(',', '').split('/')[0].strip()),
            'last_scraped': timezone.now(),
            'landlord_name': listing.get('brokerName', 'Unknown Landlord'),
            'main_image_url': listing.get('imgSrc', '')
        }
        
        # Parse address
        address_parts = listing.get('address', '').split(', ')
        if len(address_parts) >= 2:
            data['address'] = address_parts[0]
            city_state = address_parts[1].split(' ')
            data['city'] = ' '.join(city_state[:-2])
            data['state'] = city_state[-2]
            data['zip_code'] = city_state[-1]
        
        # Extract more details from the detail page if available
        if detail_soup:
            # Description
            description = detail_soup.find('div', {'data-testid': 'description'})
            if description:
                data['description'] = description.text.strip()
            
            # Property details
            facts = detail_soup.find_all('span', {'data-testid': 'fact-group-container'})
            for fact in facts:
                text = fact.text.lower()
                
                # Bedrooms
                bd_match = re.search(r'(\d+)\s*bd', text)
                if bd_match:
                    data['bedrooms'] = int(bd_match.group(1))
                
                # Bathrooms
                ba_match = re.search(r'(\d+(?:\.\d+)?)\s*ba', text)
                if ba_match:
                    data['bathrooms'] = float(ba_match.group(1))

                    # Square footage
                sqft_match = re.search(r'(\d+(?:,\d+)?)\s*sqft', text)
                if sqft_match:
                    data['square_feet'] = int(sqft_match.group(1).replace(',', ''))
            
            # Property type
            property_type_elem = detail_soup.find('span', {'data-testid': 'home-facts-summary'})
            if property_type_elem:
                type_text = property_type_elem.text.lower()
                if 'apartment' in type_text:
                    data['property_type'] = 'apartment'
                elif 'house' in type_text or 'home' in type_text:
                    data['property_type'] = 'house'
                elif 'condo' in type_text:
                    data['property_type'] = 'condo'
                elif 'townhouse' in type_text:
                    data['property_type'] = 'townhouse'
                elif 'duplex' in type_text:
                    data['property_type'] = 'duplex'
                elif 'studio' in type_text:
                    data['property_type'] = 'studio'
            
            # Available date
            available_elem = detail_soup.find('div', string=re.compile('Available'))
            if available_elem:
                date_match = re.search(r'Available\s+(\w+\s+\d+(?:,\s+\d+)?)', available_elem.text)
                if date_match:
                    try:
                        date_str = date_match.group(1)
                        if ',' not in date_str:
                            date_str += f", {datetime.now().year}"
                        data['date_available'] = datetime.strptime(date_str, '%b %d, %Y').date()
                    except ValueError:
                        pass
            
            # Images
            images = []
            img_tags = detail_soup.find_all('img', {'data-testid': 'hdp-hero-img'})
            for img in img_tags:
                if img.get('src') and img.get('src').startswith('http'):
                    images.append(img.get('src'))
            
            if images:
                data['images'] = images
            
            # Amenities
            amenities = []
            amenity_items = detail_soup.find_all('li', {'data-testid': 'feature-item'})
            for item in amenity_items:
                amenities.append(item.text.strip())
            
            if amenities:
                data['amenities'] = amenities
                
            # Voucher types - set Section 8 as default for voucher-friendly properties
            data['voucher_types'] = ['Section 8']
        
        return data