from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from listings.models import Property, Location, Landlord
import time
import logging
from django.utils import timezone
from datetime import timedelta, datetime
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def setup_driver():
    """Set up and return a configured Chrome WebDriver"""
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=options)

def get_or_create_location(city, state):
    """Helper function to get or create a Location object"""
    location, created = Location.objects.get_or_create(
        city=city,
        state=state,
        defaults={
            'country': 'United States',
            'zip_code': ''  # We don't have this info from Airbnb listings
        }
    )
    return location

def scrape_location_new_york():
    driver = setup_driver()
    try:
        url = "https://www.airbnb.com/s/New-York--NY--United-States/homes"
        driver.get(url)
        time.sleep(5)  # Wait for page to load
        
        # Wait for listings to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='card-container']"))
        )
        
        listings = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='card-container']")
        logger.info(f"Found {len(listings)} listings on page")
        
        # Get or create New York location
        ny_location = get_or_create_location('New York', 'NY')
        
        for listing in listings:
            try:
                # Get title
                title = listing.find_element(By.CSS_SELECTOR, "div[data-testid='listing-card-title']").text
                
                # Get price - try different selectors
                try:
                    price = listing.find_element(By.CSS_SELECTOR, "span[data-testid='listing-card-price']").text
                except NoSuchElementException:
                    try:
                        price = listing.find_element(By.CSS_SELECTOR, "span._1y74zjx").text
                    except NoSuchElementException:
                        price = "Price not available"
                
                # Get rating
                try:
                    rating = listing.find_element(By.CSS_SELECTOR, "span[data-testid='listing-card-rating']").text
                except NoSuchElementException:
                    rating = None
                
                # Create or update property
                property_data = {
                    'title': title,
                    'location': ny_location,
                    'rent_amount': float(price.replace('$', '').replace(',', '').split('/')[0]) if price != "Price not available" else 0,
                    'rating': float(rating.split()[0]) if rating else None,
                    'source': 'AIRBNB',
                    'is_available': True,
                    'updated_at': timezone.now()
                }
                
                Property.objects.update_or_create(
                    title=title,
                    source='AIRBNB',
                    defaults=property_data
                )
                
            except Exception as e:
                logger.error(f"Error parsing listing: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error scraping New York: {str(e)}")
    finally:
        driver.quit()

def scrape_location_chicago():
    driver = setup_driver()
    try:
        url = "https://www.airbnb.com/s/Chicago--IL--United-States/homes"
        driver.get(url)
        time.sleep(5)  # Wait for page to load
        
        # Wait for listings to load
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div[data-testid='card-container']"))
        )
        
        listings = driver.find_elements(By.CSS_SELECTOR, "div[data-testid='card-container']")
        logger.info(f"Found {len(listings)} listings on page")
        
        # Get or create Chicago location
        chicago_location = get_or_create_location('Chicago', 'IL')
        
        for listing in listings:
            try:
                # Get title
                title = listing.find_element(By.CSS_SELECTOR, "div[data-testid='listing-card-title']").text
                
                # Get price - try different selectors
                try:
                    price = listing.find_element(By.CSS_SELECTOR, "span[data-testid='listing-card-price']").text
                except NoSuchElementException:
                    try:
                        price = listing.find_element(By.CSS_SELECTOR, "span._1y74zjx").text
                    except NoSuchElementException:
                        price = "Price not available"
                
                # Get rating
                try:
                    rating = listing.find_element(By.CSS_SELECTOR, "span[data-testid='listing-card-rating']").text
                except NoSuchElementException:
                    rating = None
                
                # Create or update property
                property_data = {
                    'title': title,
                    'location': chicago_location,
                    'rent_amount': float(price.replace('$', '').replace(',', '').split('/')[0]) if price != "Price not available" else 0,
                    'rating': float(rating.split()[0]) if rating else None,
                    'source': 'AIRBNB',
                    'is_available': True,
                    'updated_at': timezone.now()
                }
                
                Property.objects.update_or_create(
                    title=title,
                    source='AIRBNB',
                    defaults=property_data
                )
                
            except Exception as e:
                logger.error(f"Error parsing listing: {str(e)}")
                continue
                
    except Exception as e:
        logger.error(f"Error scraping Chicago: {str(e)}")
    finally:
        driver.quit()

def mark_outdated_listings():
    # Mark listings as outdated if they haven't been updated in the last 7 days
    outdated_date = timezone.now() - timedelta(days=7)
    Property.objects.filter(
        updated_at__lt=outdated_date,
        is_available=True
    ).update(is_available=False)

def run_scrapers():
    total_properties = 0
    try:
        scrape_location_new_york()
        scrape_location_chicago()
        mark_outdated_listings()
        total_properties = Property.objects.filter(source='AIRBNB', is_available=True).count()
        logger.info(f"Successfully ran all scrapers. Total properties: {total_properties}")
        return total_properties
    except Exception as e:
        logger.error(f"Error running scrapers: {str(e)}")
        raise