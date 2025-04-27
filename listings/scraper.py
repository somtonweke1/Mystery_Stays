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
from datetime import timedelta

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

def scrape_location_new_york(driver, max_pages):
    listings = []
    logger.info(f"Starting scrape for New York, max pages: {max_pages}")
    # Create or get Location for New York
    location, _ = Location.objects.get_or_create(
        city="New York",
        state="NY",
        country="USA",
        defaults={'zip_code': '10001'}  # Example zip code
    )
    for page in range(1, max_pages + 1):
        url = f"https://www.airbnb.com/s/New-York--NY/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&flexible_trip_lengths%5B%5D=one_week&price_filter_input_type=0&price_filter_num_nights=5&date_picker_type=calendar&checkin=2025-05-01&checkout=2025-05-06&source=structured_search_input_header&search_type=autocomplete_click&query=New%20York%2C%20NY&place_id=ChIJOwg_06VPwokRYv534QaPC8g&page={page}"
        driver.get(url)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[itemprop="itemListElement"]'))
            )
            elements = driver.find_elements(By.CSS_SELECTOR, 'div[itemprop="itemListElement"]')
            logger.info(f"Found {len(elements)} listings on page {page}")
            for element in elements:
                try:
                    listing_id = element.find_element(By.CSS_SELECTOR, 'a').get_attribute('href').split('/')[-1]
                    title = element.find_element(By.CSS_SELECTOR, 'div[data-testid="listing-card-title"]').text
                    price = element.find_element(By.CSS_SELECTOR, 'span._tyxjp1').text
                    rating = element.find_element(By.CSS_SELECTOR, 'span.r4a59j5').text
                    # Extract host name (example selector, adjust as needed)
                    try:
                        host_name = element.find_element(By.CSS_SELECTOR, 'div[data-testid="host-name"]').text
                    except:
                        host_name = None
                    if not all([listing_id, title, price, rating]):
                        logger.warning(f"Skipping listing due to missing data: {title}")
                        continue
                    price_cleaned = float(price.replace('$', '').split('/')[0])
                    rating_cleaned = float(rating.split()[0])
                    listings.append({
                        'listing_id': listing_id,
                        'title': title,
                        'rent_amount': price_cleaned,
                        'rating': rating_cleaned,
                        'host_name': host_name
                    })
                except Exception as e:
                    logger.error(f"Error parsing element on page {page}: {e}")
                    continue
            time.sleep(2)
        except Exception as e:
            logger.error(f"Error loading page {page}: {e}")
            continue
    for listing in listings:
        try:
            # Create or get Landlord if host_name is available
            landlord = None
            if listing['host_name']:
                landlord, _ = Landlord.objects.get_or_create(name=listing['host_name'])
            Property.objects.update_or_create(
                listing_id=listing['listing_id'],  # Use listing_id as the unique identifier
                defaults={
                    'title': listing['title'],
                    'rent_amount': listing['rent_amount'],
                    'rating': listing['rating'],
                    'location': location,
                    'landlord': landlord,
                    'source': 'AIRBNB'
                }
            )
        except Exception as e:
            logger.error(f"Error saving property {listing['title']}: {e}")
    logger.info(f"Finished scraping New York. Saved {len(listings)} properties.")

def scrape_location_chicago(driver, max_pages):
    listings = []
    logger.info(f"Starting scrape for Chicago, max pages: {max_pages}")
    # Create or get Location for Chicago
    location, _ = Location.objects.get_or_create(
        city="Chicago",
        state="IL",
        country="USA",
        defaults={'zip_code': '60601'}  # Example zip code
    )
    for page in range(1, max_pages + 1):
        url = f"https://www.airbnb.com/s/Chicago--IL/homes?tab_id=home_tab&refinement_paths%5B%5D=%2Fhomes&flexible_trip_lengths%5B%5D=one_week&price_filter_input_type=0&price_filter_num_nights=5&date_picker_type=calendar&checkin=2025-05-01&checkout=2025-05-06&source=structured_search_input_header&search_type=autocomplete_click&query=Chicago%2C%20IL&place_id=ChIJ7cu8K2w0DogRAMY2XzZ5z-Y&page={page}"
        driver.get(url)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[itemprop="itemListElement"]'))
            )
            elements = driver.find_elements(By.CSS_SELECTOR, 'div[itemprop="itemListElement"]')
            logger.info(f"Found {len(elements)} listings on page {page}")
            for element in elements:
                try:
                    listing_id = element.find_element(By.CSS_SELECTOR, 'a').get_attribute('href').split('/')[-1]
                    title = element.find_element(By.CSS_SELECTOR, 'div[data-testid="listing-card-title"]').text
                    price = element.find_element(By.CSS_SELECTOR, 'span._tyxjp1').text
                    rating = element.find_element(By.CSS_SELECTOR, 'span.r4a59j5').text
                    try:
                        host_name = element.find_element(By.CSS_SELECTOR, 'div[data-testid="host-name"]').text
                    except:
                        host_name = None
                    if not all([listing_id, title, price, rating]):
                        logger.warning(f"Skipping listing due to missing data: {title}")
                        continue
                    price_cleaned = float(price.replace('$', '').split('/')[0])
                    rating_cleaned = float(rating.split()[0])
                    listings.append({
                        'listing_id': listing_id,
                        'title': title,
                        'rent_amount': price_cleaned,
                        'rating': rating_cleaned,
                        'host_name': host_name
                    })
                except Exception as e:
                    logger.error(f"Error parsing element on page {page}: {e}")
                    continue
            time.sleep(2)
        except Exception as e:
            logger.error(f"Error loading page {page}: {e}")
            continue
    for listing in listings:
        try:
            landlord = None
            if listing['host_name']:
                landlord, _ = Landlord.objects.get_or_create(name=listing['host_name'])
            Property.objects.update_or_create(
                listing_id=listing['listing_id'],  # Use listing_id as the unique identifier
                defaults={
                    'title': listing['title'],
                    'rent_amount': listing['rent_amount'],
                    'rating': listing['rating'],
                    'location': location,
                    'landlord': landlord,
                    'source': 'AIRBNB'
                }
            )
        except Exception as e:
            logger.error(f"Error saving property {listing['title']}: {e}")
    logger.info(f"Finished scraping Chicago. Saved {len(listings)} properties.")

def run_all_scrapers(locations, max_pages):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    try:
        for location in locations:
            if location.lower() == "new york":
                scrape_location_new_york(driver, max_pages)
            elif location.lower() == "chicago":
                scrape_location_chicago(driver, max_pages)
    finally:
        driver.quit()

def mark_outdated_listings():
    threshold = timezone.now() - timedelta(days=7)
    outdated_properties = Property.objects.filter(updated_at__lt=threshold)
    for prop in outdated_properties:
        prop.is_outdated = True
        prop.save()
    logger.info(f"Marked {outdated_properties.count()} properties as outdated.")