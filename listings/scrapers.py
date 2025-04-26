# listings/scrapers.py

import logging

# Assuming you have scraper functions for each location
from . import scrape_location_new_york, scrape_location_chicago

logger = logging.getLogger(__name__)

def run_all_scrapers(locations=None, max_pages=None):
    """
    Run scrapers for the provided locations and max_pages.
    :param locations: List of location names to scrape
    :param max_pages: Maximum number of pages to scrape for each location
    :return: Results of the scrapers
    """
    if not locations:
        logger.error("No locations provided for scraping.")
        return
    
    results = []
    for location in locations:
        try:
            logger.info(f"Starting scraper for {location}...")
            if location.lower() == "new york":
                results.append(scrape_location_new_york(max_pages))
            elif location.lower() == "chicago":
                results.append(scrape_location_chicago(max_pages))
            else:
                logger.warning(f"No scraper defined for {location}.")
        except Exception as e:
            logger.error(f"Error occurred while scraping {location}: {e}")
    
    return results
