from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
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
import json

# Create the Flask app
app = Flask(__name__)
CORS(app)

# Create directory for screenshots if it doesn't exist
os.makedirs('debug', exist_ok=True)

# Mock database for simplicity
mock_db = {
    'properties': {},
    'users': {},
    'bookings': {}
}

# Root route
@app.route("/")
def home():
    return "Mystery Stays API is running!"

# Mock implementation of MysteryStayAgent for simplicity
class MysteryStayAgent:
    def add_available_property(self, data):
        property_id = str(len(mock_db['properties']) + 1)
        mock_db['properties'][property_id] = data
        return property_id

    def register_user_preferences(self, user_id, preferences):
        if user_id not in mock_db['users']:
            mock_db['users'][user_id] = {}
        mock_db['users'][user_id]['preferences'] = preferences
        return True

    def match_user_to_properties(self, user_id):
        # Simple mock implementation
        return list(mock_db['properties'].values())[:3]

    def book_mystery_stay(self, user_id, property_id, check_in, check_out):
        booking_id = str(len(mock_db['bookings']) + 1)
        mock_db['bookings'][booking_id] = {
            'user_id': user_id,
            'property_id': property_id,
            'check_in': str(check_in),
            'check_out': str(check_out),
            'status': 'confirmed'
        }
        return {'booking_id': booking_id, 'status': 'confirmed'}

    def reveal_location(self, booking_id):
        if booking_id in mock_db['bookings']:
            property_id = mock_db['bookings'][booking_id]['property_id']
            return mock_db['properties'][property_id]
        return {'error': 'Booking not found'}

# Initialize agent
agent = MysteryStayAgent()

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
    
    # Calculate check-in date 3 months from now for peak season comparison
    try:
        check_in_date = datetime.datetime.strptime(check_in, "%Y-%m-%d")
        peak_date = check_in_date + datetime.timedelta(days=90)
        peak_check_in = peak_date.strftime("%Y-%m-%d")
        peak_check_out = (peak_date + datetime.timedelta(days=(datetime.datetime.strptime(check_out, "%Y-%m-%d") - check_in_date).days)).strftime("%Y-%m-%d")
    except:
        # Fallback dates if parsing fails
        peak_check_in = "2025-08-01"
        peak_check_out = "2025-08-05"
    
    options = Options()
    options.add_argument('--headless=new')
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
        screenshot_path = os.path.join("debug", f"airbnb_{int(time.time())}.png")
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        # Use multiple possible selectors with fallbacks
        listing_selectors = [
            '[itemprop="itemListElement"]',
            'div[data-testid="card-container"]',
            '.c4mnd7m',  # Another possible Airbnb listing container class
            '.cy5jw6o',  # Another possible Airbnb listing container class
            '.gh7uyir',   # Another possible newer class
            'div[aria-label="Listing"]', # Another possible selector
            '.gycj8f5'  # Another possible selector
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
                            for title_selector in ['[data-testid="listing-card-title"]', '.t1jojoys', '.a8jt5op', '.t12u7nq4', 'h3']:
                                try:
                                    title_elem = elem.find_element(By.CSS_SELECTOR, title_selector)
                                    title = title_elem.text
                                    if title:
                                        break
                                except:
                                    continue
                            
                            # Multiple possible price selectors
                            price = None
                            for price_selector in ['._1y74zjx', '._tyxjp1', '.a8jt5op', '.pquyp1l', '[data-testid="price-element"]', '.prqafc0', 'span[aria-hidden="true"]']:
                                try:
                                    price_elem = elem.find_element(By.CSS_SELECTOR, price_selector)
                                    price = price_elem.text
                                    if price and ('$' in price or '€' in price):
                                        break
                                except:
                                    continue
                            
                            if title and price:
                                # Extract numeric price value
                                price_text = price.split('$')[1] if '$' in price else price
                                price_digits = ''.join(filter(str.isdigit, price_text))
                                if price_digits:
                                    price_val = int(price_digits)
                                    
                                    # Apply 50% discount for mystery stays
                                    discounted = round(price_val * 0.5)
                                    
                                    # Generate additional info for a better demo
                                    # Just for demonstration - in real app you'd scrape this or use an API
                                    rating = round(4.0 + (hash(title) % 10) / 10, 1)  # Rating between 4.0-4.9
                                    reviews = 10 + (hash(title) % 90)  # Between 10-99 reviews
                                    
                                    listing_data = {
                                        "title": title,
                                        "original_price": price_val,
                                        "discount_price": discounted, 
                                        "city": city,
                                        "rating": rating,
                                        "reviews": reviews
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
                                    
                                    # Try to get image if available
                                    try:
                                        img_element = elem.find_element(By.CSS_SELECTOR, 'img')
                                        img_src = img_element.get_attribute('src')
                                        if img_src:
                                            listing_data["image"] = img_src
                                    except:
                                        pass
                                    
                                    listings.append(listing_data)
                                    print(f"Added listing: {title}, Price: {price_val}, Discounted: {discounted}")
                        except Exception as e:
                            print(f"Error processing individual listing: {str(e)}")
                            continue
                    
                    # If we found listings with this selector, break the loop
                    if listings:
                        break
            except Exception as e:
                print(f"Selector {selector} failed: {str(e)}")
                continue

        # If scraping failed, use mock data for development/testing
        if not listings:
            print("No listings found with standard selectors, using mock data...")
            listings = [
                {
                    "title": "Cozy Apartment in Downtown",
                    "original_price": 150,
                    "discount_price": 75,
                    "city": city,
                    "rating": 4.8,
                    "reviews": 65,
                    "image": "https://a0.muscache.com/im/pictures/miso/Hosting-53455243/original/a13c3824-3904-49f9-9a1d-2bd1ac33eb80.jpeg",
                    "url": "https://www.airbnb.com/rooms/53455243"
                },
                {
                    "title": "Luxury Penthouse with Ocean View",
                    "original_price": 320,
                    "discount_price": 160,
                    "city": city,
                    "rating": 4.9,
                    "reviews": 87,
                    "image": "https://a0.muscache.com/im/pictures/miso/Hosting-25244023/original/e9d4dc69-a550-4142-b6f4-e358d0246fa4.jpeg",
                    "url": "https://www.airbnb.com/rooms/25244023"
                },
                {
                    "title": "Charming Studio near Historic Center",
                    "original_price": 95,
                    "discount_price": 47,
                    "city": city,
                    "rating": 4.7,
                    "reviews": 42,
                    "image": "https://a0.muscache.com/im/pictures/miso/Hosting-23206143/original/e83a7404-29f5-4bef-bcfe-36d14eb24896.jpeg",
                    "url": "https://www.airbnb.com/rooms/23206143"
                },
                {
                    "title": "Modern Loft with City Views",
                    "original_price": 180,
                    "discount_price": 90,
                    "city": city,
                    "rating": 4.6,
                    "reviews": 39,
                    "image": "https://a0.muscache.com/im/pictures/monet/Luxury-670175052477992044/original/2aae71d9-6d89-4350-8db1-30f4c9af5ab7",
                    "url": "https://www.airbnb.com/rooms/670175052477992044"
                },
                {
                    "title": "Beachfront Villa with Private Pool",
                    "original_price": 450,
                    "discount_price": 225,
                    "city": city,
                    "rating": 4.9,
                    "reviews": 124,
                    "image": "https://a0.muscache.com/im/pictures/4a5f0912-28cc-4355-80a1-b1a3d55a3976.jpg",
                    "url": "https://www.airbnb.com/rooms/4a5f0912"
                }
            ]
        
        # Sort listings by discount_price (cheapest first)
        listings.sort(key=lambda x: x["discount_price"])
                
        driver.quit()
        
        return jsonify({"status": "success", "listings": listings})
    except Exception as e:
        print(f"Fatal error in scan_airbnb: {str(e)}")
        # Try to close driver in case of exception
        try:
            if 'driver' in locals() and driver:
                driver.quit()
        except:
            pass
        # Return mock data on error for development/testing
        mock_listings = [
            {
                "title": "Charming Studio near Historic Center",
                "original_price": 95,
                "discount_price": 47,
                "city": city,
                "rating": 4.7,
                "reviews": 42,
                "image": "https://a0.muscache.com/im/pictures/miso/Hosting-23206143/original/e83a7404-29f5-4bef-bcfe-36d14eb24896.jpeg",
                "url": "https://www.airbnb.com/rooms/23206143"
            },
            {
                "title": "Cozy Apartment in Downtown",
                "original_price": 150,
                "discount_price": 75,
                "city": city,
                "rating": 4.8,
                "reviews": 65,
                "image": "https://a0.muscache.com/im/pictures/miso/Hosting-53455243/original/a13c3824-3904-49f9-9a1d-2bd1ac33eb80.jpeg",
                "url": "https://www.airbnb.com/rooms/53455243"
            },
            {
                "title": "Modern Loft with City Views",
                "original_price": 180,
                "discount_price": 90,
                "city": city,
                "rating": 4.6,
                "reviews": 39,
                "image": "https://a0.muscache.com/im/pictures/monet/Luxury-670175052477992044/original/2aae71d9-6d89-4350-8db1-30f4c9af5ab7",
                "url": "https://www.airbnb.com/rooms/670175052477992044"
            },
            {
                "title": "Luxury Penthouse with Ocean View",
                "original_price": 320,
                "discount_price": 160,
                "city": city,
                "rating": 4.9,
                "reviews": 87,
                "image": "https://a0.muscache.com/im/pictures/miso/Hosting-25244023/original/e9d4dc69-a550-4142-b6f4-e358d0246fa4.jpeg",
                "url": "https://www.airbnb.com/rooms/25244023"
            }
        ]
        # Sort mock listings by discount_price as well
        mock_listings.sort(key=lambda x: x["discount_price"])
        return jsonify({"status": "success", "listings": mock_listings})

# Frontend HTML
@app.route('/frontend')
def serve_frontend():
    html_content = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mystery Stays - Find Hidden Discounts</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            line-height: 1.6;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            color: #333;
            background-color: #f5f5f5;
        }
        header {
            text-align: center;
            padding: 20px 0;
            border-bottom: 1px solid #eee;
            margin-bottom: 30px;
        }
        h1 {
            color: #2c3e50;
        }
        .search-container {
            background: #fff;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        .form-group {
            margin-bottom: 15px;
        }
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
        }
        input, select {
            width: 100%;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 16px;
        }
        button {
            background: #3498db;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 16px;
            width: 100%;
        }
        button:hover {
            background: #2980b9;
        }
        .results-container {
            margin-top: 30px;
        }
        .loading {
            text-align: center;
            display: none;
        }
        .loading-spinner {
            border: 5px solid #f3f3f3;
            border-top: 5px solid #3498db;
            border-radius: 50%;
            width: 50px;
            height: 50px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .listing-card {
            background: #fff;
            border: 1px solid #eee;
            border-radius: 8px;
            margin-bottom: 20px;
            overflow: hidden;
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }
        .listing-image {
            height: 220px;
            overflow: hidden;
            position: relative;
            cursor: pointer;
        }
        .listing-image img {
            width: 100%;
            height: 100%;
            object-fit: cover;
        }
        .listing-details {
            padding: 15px;
        }
        .listing-title {
            font-size: 18px;
            font-weight: bold;
            margin-bottom: 10px;
            cursor: pointer;
            color: #2c3e50;
        }
        .listing-title:hover {
            color: #3498db;
            text-decoration: underline;
        }
        .listing-meta {
            display: flex;
            justify-content: space-between;
            margin-bottom: 15px;
        }
        .listing-location {
            color: #777;
        }
        .listing-rating {
            display: flex;
            align-items: center;
        }
        .star {
            color: #ff385c;
            margin-right: 5px;
        }
        .listing-pricing {
            display: flex;
            justify-content: space-between;
            align-items: flex-end;
            border-top: 1px solid #eee;
            padding-top: 15px;
        }
        .price-container {
            text-align: right;
        }
        .original-price {
            text-decoration: line-through;
            color: #999;
            font-size: 14px;
        }
        .discount-price {
            font-weight: bold;
            color: #ff385c;
            font-size: 22px;
        }
        .discount-badge {
            background: #ff385c;
            color: white;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 0.8em;
            margin-left: 5px;
        }
        .book-btn {
            background: #ff385c;
            color: white;
            border: none;
            padding: 10px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-weight: bold;
        }
        .book-btn:hover {
            background: #e0314f;
        }
        .no-results {
            text-align: center;
            padding: 30px;
            background: #fff;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: none;
        }
        .view-listing {
            font-size: 14px;
            color: #3498db;
            text-decoration: underline;
            cursor: pointer;
            display: inline-block;
            margin-left: 10px;
            vertical-align: middle;
        }
        .view-listing:hover {
            color: #2980b9;
        }
        .listing-action-area {
            display: flex;
            align-items: center;
        }
        .sort-info {
            background-color: #e8f4f8;
            padding: 10px 15px;
            border-radius: 4px;
            margin-bottom: 15px;
            font-size: 14px;
            color: #2980b9;
            display: none;
        }
    </style>
</head>
<body>
    <header>
        <h1>Mystery Stays</h1>
        <p>Find hidden discounts on Airbnb listings with last-minute availability</p>
    </header>

    <div class="search-container">
        <form id="search-form">
            <div class="form-group">
                <label for="city">Destination</label>
                <input type="text" id="city" placeholder="Enter city name" value="Lisbon" required>
            </div>
            <div class="form-group">
                <label for="check-in">Check-in Date</label>
                <input type="date" id="check-in" required>
            </div>
            <div class="form-group">
                <label for="check-out">Check-out Date</label>
                <input type="date" id="check-out" required>
            </div>
            <button type="submit" id="search-button">Find Mystery Deals</button>
        </form>
    </div>

    <div class="loading">
        <p>Scanning for the best hidden deals...</p>
        <div class="loading-spinner"></div>
    </div>

    <div class="no-results">
        <h3>No discounted listings found</h3>
        <p>Try different dates or another destination</p>
    </div>

    <div class="sort-info">
        Showing results sorted by price: cheapest first
    </div>

    <div class="results-container" id="results"></div>

    <script>
        // Set default dates (today and 5 days from now)
        const today = new Date();
        const fiveDaysLater = new Date(today);
        fiveDaysLater.setDate(today.getDate() + 5);
        
        document.getElementById('check-in').valueAsDate = today;
        document.getElementById('check-out').valueAsDate = fiveDaysLater;

        document.getElementById('search-form').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const city = document.getElementById('city').value;
            const checkIn = document.getElementById('check-in').value;
            const checkOut = document.getElementById('check-out').value;
            
            // Show loading
            document.querySelector('.loading').style.display = 'block';
            document.querySelector('.no-results').style.display = 'none';
            document.querySelector('.sort-info').style.display = 'none';
            document.getElementById('results').innerHTML = '';
            
            try {
                const response = await fetch('http://127.0.0.1:5001/scan_airbnb', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        city: city,
                        check_in: checkIn,
                        check_out: checkOut
                    })
                });
                
                const data = await response.json();
                
                // Hide loading
                document.querySelector('.loading').style.display = 'none';
                
                if (data.status === 'success' && data.listings && data.listings.length > 0) {
                    // Show the sort information
                    document.querySelector('.sort-info').style.display = 'block';
                    displayResults(data.listings);
                } else {
                    document.querySelector('.no-results').style.display = 'block';
                }
            } catch (error) {
                console.error('Error:', error);
                document.querySelector('.loading').style.display = 'none';
                document.querySelector('.no-results').style.display = 'block';
                document.querySelector('.no-results h3').textContent = 'Error scanning listings';
                document.querySelector('.no-results p').textContent = 'Please try again later';
            }
        });

        function displayResults(listings) {
            const resultsContainer = document.getElementById('results');
            
            listings.forEach(listing => {
                const discountPercentage = Math.round(((listing.original_price - listing.discount_price) / listing.original_price) * 100);
                
                const listingCard = document.createElement('div');
                listingCard.className = 'listing-card';
                
                // Default image if none provided
                const imageUrl = listing.image || 'https://a0.muscache.com/im/pictures/e25a9b25-fa98-4160-bfd1-039287bf38b6.jpg';
                
                listingCard.innerHTML = `
                    <div class="listing-image">
                        <img src="${imageUrl}" alt="${listing.title}">
                    </div>
                    <div class="listing-details">
                        <div class="listing-title">${listing.title}</div>
                        <div class="listing-meta">
                            <div class="listing-location">${listing.city}</div>
                            <div class="listing-rating">
                                <span class="star">★</span>
                                ${listing.rating || 4.8} (${listing.reviews || 42} reviews)
                            </div>
                        </div>
                        <div class="listing-pricing">
                            <div class="listing-action-area">
                                <button class="book-btn">Book Mystery Stay</button>
                                ${listing.url ? `<span class="view-listing">View on Airbnb</span>` : ''}
                            </div>
                            <div class="price-container">
                                <div class="original-price">$${listing.original_price}</div>
                                <div class="discount-price">$${listing.discount_price} <span class="discount-badge">${discountPercentage}% OFF</span></div>
                            </div>
                        </div>
                    </div>
                `;
                
                // Add event listener to the book button
                const bookButton = listingCard.querySelector('.book-btn');
                bookButton.addEventListener('click', function() {
                    alert(`You're booking a Mystery Stay at "${listing.title}" for $${listing.discount_price}!`);
                    // Here you could implement actual booking logic or redirect to booking page
                });
                
                // Add click events to view the original listing
                if (listing.url) {
                    // Add click event to the "View on Airbnb" link
                    const viewLink = listingCard.querySelector('.view-listing');
                    viewLink.addEventListener('click', function() {
                        window.open(listing.url, '_blank');
                    });
                    
                    // Also make the title and image clickable to view original listing
                    const titleElem = listingCard.querySelector('.listing-title');
                    titleElem.addEventListener('click', function() {
                        window.open(listing.url, '_blank');
                    });
                    
                    const imageContainer = listingCard.querySelector('.listing-image');
                    imageContainer.addEventListener('click', function() {
                        window.open(listing.url, '_blank');
                    });
                }
                
                resultsContainer.appendChild(listingCard);
            });
        }
    </script>
</body>
</html>
    """
    return html_content

# Serve debug images
@app.route('/debug/<path:filename>')
def serve_debug_image(filename):
    return send_from_directory('debug', filename)

if __name__ == '__main__':
    app.run(port=5001, debug=True)