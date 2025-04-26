import logging
from django.utils import timezone
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

def run_all_scrapers(locations=None, max_pages=2):
    """
    Run all property scrapers for the given locations
    
    Args:
        locations: List of locations to search (cities or ZIP codes)
        max_pages: Maximum number of pages to scrape per location and source
    
    Returns:
        Dict with counts of properties found per source
    """
    from .zillow import ZillowScraper
    from .apartments import ApartmentsDotComScraper
    
    if locations is None:
        locations = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix"]
    
    results = {
        'zillow': 0,
        'apartments': 0,
        'total': 0
    }
    
    # Scrape Zillow
    try:
        zillow = ZillowScraper()
        for location in locations:
            properties = zillow.scrape_listings(location=location, max_pages=max_pages)
            results['zillow'] += len(properties)
            results['total'] += len(properties)
            logger.info(f"Found {len(properties)} voucher-friendly properties on Zillow in {location}")
    except Exception as e:
        logger.error(f"Error scraping Zillow: {str(e)}")
    
    # Scrape Apartments.com
    try:
        apartments = ApartmentsDotComScraper()
        for location in locations:
            properties = apartments.scrape_listings(location=location, max_pages=max_pages)
            results['apartments'] += len(properties)
            results['total'] += len(properties)
            logger.info(f"Found {len(properties)} voucher-friendly properties on Apartments.com in {location}")
    except Exception as e:
        logger.error(f"Error scraping Apartments.com: {str(e)}")
    
    return results


def mark_outdated_listings(days=30):
    """
    Mark properties as unavailable if they haven't been updated in the specified days
    
    Args:
        days: Number of days after which a listing is considered outdated
    
    Returns:
        Number of properties marked as unavailable
    """
    from listings.models import Property
    
    cutoff_date = timezone.now() - timedelta(days=days)
    outdated = Property.objects.filter(
        is_available=True,
        last_scraped__lt=cutoff_date
    )
    
    count = outdated.count()
    outdated.update(is_available=False)
    
    logger.info(f"Marked {count} properties as unavailable (not updated in {days} days)")
    return count