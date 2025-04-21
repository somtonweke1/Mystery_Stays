from flask import Flask, request, jsonify
from flask_cors import CORS
from Core_Functionality import MysteryStayAgent
import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

app = Flask(__name__)
CORS(app)
agent = MysteryStayAgent()  # Ensure this import works

@app.route('/properties/add', methods=['POST'])
def add_property():
    data = request.json
    property_id = agent.add_available_property(data)
    return jsonify({"status": "success", "property_id": property_id})

@app.route('/users/preferences', methods=['POST'])
def register_preferences():
    data = request.json
    user_id = data.get("user_id")
    preferences = data.get("preferences")
    agent.register_user_preferences(user_id, preferences)
    return jsonify({"status": "success"})

@app.route('/properties/match/<user_id>', methods=['GET'])
def match_properties(user_id):
    matches = agent.match_user_to_properties(user_id)
    return jsonify({"status": "success", "matches": matches})

@app.route('/bookings/create', methods=['POST'])
def book_property():
    data = request.json
    user_id = data.get("user_id")
    property_id = data.get("property_id")
    check_in = datetime.datetime.strptime(data.get("check_in"), "%Y-%m-%d").date()
    check_out = datetime.datetime.strptime(data.get("check_out"), "%Y-%m-%d").date()
    confirmation = agent.book_mystery_stay(user_id, property_id, check_in, check_out)
    return jsonify(confirmation)

@app.route('/bookings/reveal/<booking_id>', methods=['GET'])
def reveal_booking(booking_id):
    details = agent.reveal_location(booking_id)
    return jsonify(details)

@app.route('/scan_airbnb', methods=['POST'])
def scan_airbnb():
    data = request.json
    city = data.get('city', 'Lisbon')
    check_in = data.get('check_in', '2025-05-01')
    check_out = data.get('check_out', '2025-05-05')
    
    options = Options()
    options.add_argument('--headless=new')  # Updated headless mode
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36')
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    
    try:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        # Execute stealth JS script to avoid detection
        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        # Properly formatted URL with encoded city name
        encoded_city = city.replace(' ', '%20')
        url = f"https://www.airbnb.com/s/{encoded_city}/homes?checkin={check_in}&checkout={check_out}&adults=1"
        
        print(f"Attempting to access URL: {url}")
        driver.get(url)
        
        # Add a longer wait time for page load
        time.sleep(5)
        
        # Save screenshot for debugging
        screenshot_path = os.path.join(os.getcwd(), "airbnb_debug.png")
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        # Use multiple possible selectors with fallbacks for listings
        listing_selectors = [
            '[itemprop="itemListElement"]',
            'div[data-testid="card-container"]',
            '.c4mnd7m',  # Another possible Airbnb listing container class
            '.cy5jw6o',  # Another possible Airbnb listing container class
            '.gh7uyir'   # Another possible newer class
        ]
        
        # Try each selector
        listings = []
        for selector in listing_selectors:
            try:
                print(f"Trying selector: {selector}")
                elements = WebDriverWait(driver, 10).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                )
                if elements:
                    print(f"Found {len(elements)} listings with selector {selector}")
                    
                    for elem in elements[:10]:
                        try:
                            # Multiple possible title selectors
                            title = None
                            for title_selector in ['[data-testid="listing-card-title"]', '.t1jojoys', '.a8jt5op', '.t12u7nq4']:
                                try:
                                    title_elem = elem.find_element(By.CSS_SELECTOR, title_selector)
                                    title = title_elem.text
                                    if title:
                                        break
                                except:
                                    continue
                            
                            # Multiple possible price selectors
                            price = None
                            for price_selector in ['._1y74zjx', '._tyxjp1', '.a8jt5op', '.pquyp1l', '[data-testid="price-element"]', '.prqafc0']:
                                try:
                                    price_elem = elem.find_element(By.CSS_SELECTOR, price_selector)
                                    price = price_elem.text
                                    if price:
                                        break
                                except:
                                    continue
                            
                            if title and price:
                                # Extract numeric price value
                                price_text = price.split('$')[1] if '$' in price else price
                                # More robust price extraction
                                price_digits = ''.join(filter(str.isdigit, price_text))
                                if price_digits:
                                    price_val = int(price_digits)
                                    discounted = round(price_val * 0.5)
                                    
                                    listing_data = {
                                        "title": title,
                                        "original_price": price_val,
                                        "discount_price": discounted,
                                        "city": city
                                    }
                                    
                                    # Try to get the URL if possible
                                    try:
                                        link_element = elem.find_element(By.CSS_SELECTOR, 'a')
                                        if link_element:
                                            href = link_element.get_attribute('href')
                                            if href:
                                                listing_data["url"] = href
                                    except:
                                        pass
                                    
                                    listings.append(listing_data)
                                    print(f"Added listing: {title}, Price: {price_val}")
                        except Exception as e:
                            print(f"Error processing individual listing: {str(e)}")
                            continue
                    
                    # If we found listings with this selector, break the loop
                    if listings:
                        break
            except Exception as e:
                print(f"Selector {selector} failed: {str(e)}")
                continue
                
        # Before quitting, if no listings found, try a different approach
        if not listings:
            print("No listings found with standard selectors, trying alternative approach...")
            try:
                # Try looking for any pricing elements on the page
                price_elements = driver.find_elements(By.CSS_SELECTOR, 'span[aria-hidden="true"]')
                for element in price_elements:
                    price_text = element.text
                    if '$' in price_text or '€' in price_text:
                        print(f"Found potential price: {price_text}")
                        # Look for nearby elements that might contain titles
                        parent = element
                        for _ in range(5):  # Look up to 5 levels up
                            if parent:
                                parent = parent.find_element(By.XPATH, '..')
                                potential_title = parent.text.split('\n')[0] if parent and '\n' in parent.text else None
                                if potential_title and len(potential_title) > 5:
                                    price_digits = ''.join(filter(str.isdigit, price_text))
                                    if price_digits:
                                        price_val = int(price_digits)
                                        discounted = round(price_val * 0.5)
                                        listings.append({
                                            "title": potential_title[:50],  # Limit title length
                                            "original_price": price_val,
                                            "discount_price": discounted,
                                            "city": city
                                        })
                                        print(f"Added listing using alternative method: {potential_title[:50]}")
                                        if len(listings) >= 10:
                                            break
                            else:
                                break
            except Exception as e:
                print(f"Alternative approach failed: {str(e)}")
        
        driver.quit()
        
        if not listings:
            print("No listings found. Page might be blocked or structure changed.")
            
        return jsonify({"status": "success", "listings": listings})
    except Exception as e:
        print(f"Fatal error in scan_airbnb: {str(e)}")
        # Try to close driver in case of exception
        try:
            if 'driver' in locals() and driver:
                driver.quit()
        except:
            pass
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/")
def home():
    return "Mystery Stays API is running!"

if __name__ == '__main__':
    app.run(port=5001, debug=True)