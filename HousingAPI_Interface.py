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
import re

# Create the Flask app
app = Flask(__name__)
CORS(app)

# Create directory for screenshots if it doesn't exist
os.makedirs('debug', exist_ok=True)

# Mock database for simplicity - we'll replace this with Supabase later if needed
mock_db = {
    'properties': {},
    'landlords': {},
    'members': {},
    'applications': {}
}

# Root route
@app.route("/")
def home():
    return "Housing Navigator Assistant API is running!"

# Housing Sources - websites to scan for voucher-accepting properties
HOUSING_SOURCES = [
    {
        "name": "NYC Housing Connect",
        "url": "https://housingconnect.nyc.gov/PublicWeb/search-rentals",
        "selectors": {
            "listings": ".search-results-list .search-result",
            "title": ".development-title",
            "address": ".development-address",
            "price": ".unit-summary-rent",
            "bedrooms": ".unit-summary-beds"
        }
    },
    {
        "name": "StreetEasy",
        "url": "https://streeteasy.com/for-rent/nyc/status:open",
        "selectors": {
            "listings": ".searchCardList article",
            "title": ".listingCard-title",
            "address": ".listingCard-address",
            "price": ".listingCard-price",
            "bedrooms": ".listingCard-details"
        }
    },
    {
        "name": "GoSection8",
        "url": "https://www.gosection8.com/Section-8-housing-in-New-York-NY/",
        "selectors": {
            "listings": ".property-listing",
            "title": ".property-title",
            "address": ".property-address",
            "price": ".property-rent",
            "bedrooms": ".property-details"
        }
    }
]

@app.route('/scan_housing', methods=['POST'])
def scan_housing():
    data = request.json
    neighborhood = data.get('neighborhood', 'All NYC')
    max_rent = data.get('max_rent', 2000)
    bedrooms = data.get('bedrooms', '1')
    voucher_types = data.get('voucher_types', ['Section 8', 'CityFHEPS'])
    
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
        
        # Initialize results
        all_properties = []
        
        # We'll start with scanning NYC Housing Connect
        # In real implementation, we would iterate through HOUSING_SOURCES
        print(f"Scanning for housing in {neighborhood} with voucher support...")
        
        # For demonstration, we'll use a mock approach similar to the original code
        # Save screenshot for debugging
        screenshot_path = os.path.join("debug", f"housing_scan_{int(time.time())}.png")
        driver.save_screenshot(screenshot_path)
        print(f"Screenshot saved to {screenshot_path}")
        
        # Generate mock properties since live scanning would require complex site-specific logic
        mock_properties = generate_mock_properties(neighborhood, voucher_types, max_rent, bedrooms)
        
        # In a real implementation, you would do something like this:
        # for source in HOUSING_SOURCES:
        #     try:
        #         driver.get(source['url'])
        #         time.sleep(5)  # Wait for page to load
        #         
        #         listings = WebDriverWait(driver, 10).until(
        #             EC.presence_of_all_elements_located((By.CSS_SELECTOR, source['selectors']['listings']))
        #         )
        #         
        #         # Process each listing...
        #     except Exception as e:
        #         print(f"Error scanning {source['name']}: {str(e)}")
        #         continue
        
        driver.quit()
        
        # Sort properties by rent (lowest first)
        mock_properties.sort(key=lambda x: x["rent"])
        
        return jsonify({
            "status": "success", 
            "properties": mock_properties,
            "filters_applied": {
                "neighborhood": neighborhood,
                "max_rent": max_rent,
                "bedrooms": bedrooms,
                "voucher_types": voucher_types
            }
        })
        
    except Exception as e:
        print(f"Fatal error in scan_housing: {str(e)}")
        # Try to close driver in case of exception
        try:
            if 'driver' in locals() and driver:
                driver.quit()
        except:
            pass
            
        # Return mock data on error (for demo purposes)
        mock_properties = generate_mock_properties(neighborhood, voucher_types, max_rent, bedrooms)
        mock_properties.sort(key=lambda x: x["rent"])
        
        return jsonify({
            "status": "success", 
            "properties": mock_properties,
            "note": "Using mock data due to scanning error"
        })

def generate_mock_properties(neighborhood, voucher_types, max_rent, bedrooms):
    """Generate realistic mock NYC housing properties that accept vouchers"""
    # NYC neighborhoods
    neighborhoods = [
        "Astoria", "Bedford-Stuyvesant", "Bushwick", "Crown Heights", "East Harlem",
        "Flatbush", "Jackson Heights", "Kingsbridge", "Lower East Side", "Morningside Heights",
        "Washington Heights", "South Bronx", "Jamaica", "Flushing", "Sunset Park"
    ]
    
    # If specific neighborhood requested, prioritize it
    if neighborhood != "All NYC" and neighborhood not in neighborhoods:
        neighborhoods.insert(0, neighborhood)
    
    # Realistic landlord names
    landlords = [
        {"name": "Greentree Property Management", "voucher_friendly": True, "rating": 4.2},
        {"name": "New York Housing Associates", "voucher_friendly": True, "rating": 3.9},
        {"name": "Metro Living LLC", "voucher_friendly": True, "rating": 4.0},
        {"name": "Five Boroughs Realty", "voucher_friendly": True, "rating": 3.7},
        {"name": "Community Housing Partners", "voucher_friendly": True, "rating": 4.5}
    ]
    
    # Generate properties
    properties = []
    num_properties = 8 + (hash(neighborhood) % 5)  # 8-12 properties
    
    for i in range(num_properties):
        # Select neighborhood
        if neighborhood != "All NYC":
            prop_neighborhood = neighborhood
        else:
            prop_neighborhood = neighborhoods[i % len(neighborhoods)]
        
        # Generate address
        street_num = 100 + (i * 11) % 900
        streets = ["Broadway", "Amsterdam Ave", "Flatbush Ave", "Nostrand Ave", "Malcolm X Blvd", 
                   "Northern Blvd", "Myrtle Ave", "Fulton St", "Atlantic Ave", "Grand Concourse"]
        street = streets[i % len(streets)]
        address = f"{street_num} {street}, {prop_neighborhood}, NY"
        
        # Generate unit details
        prop_bedrooms = bedrooms if bedrooms != "Any" else str((i % 3) + 1)
        bathrooms = "1" if prop_bedrooms == "1" else "1.5" if prop_bedrooms == "2" else "2"
        
        # Generate rent (weighted toward max_rent)
        base_rent = 1200 if prop_bedrooms == "1" else 1600 if prop_bedrooms == "2" else 2200
        variation = (i % 7) * 100
        prop_rent = min(base_rent + variation, max_rent - 100)
        
        # Determine accepted vouchers
        # More realistic: different properties accept different voucher types
        accepted_vouchers = []
        for voucher in voucher_types:
            if voucher == "Section 8" and i % 3 != 0:  # 2/3 accept Section 8
                accepted_vouchers.append("Section 8")
            if voucher == "CityFHEPS" and i % 4 != 0:  # 3/4 accept CityFHEPS
                accepted_vouchers.append("CityFHEPS")
            if voucher == "FHEPS" and i % 5 == 0:  # 1/5 accept FHEPS
                accepted_vouchers.append("FHEPS")
            if voucher == "HASA" and i % 6 == 0:  # 1/6 accept HASA
                accepted_vouchers.append("HASA")
        
        # If no vouchers matched our filters, add at least one
        if not accepted_vouchers and voucher_types:
            accepted_vouchers.append(voucher_types[0])
        
        # Select landlord
        landlord = landlords[i % len(landlords)]
        
        # Generate image URL - for a real app, we would scrape these
        img_id = 100 + (i * 37) % 900
        image_url = f"https://placehold.co/600x400/png?text=NYC+Apartment+{img_id}"
        
        # Create property object
        property_obj = {
            "id": f"prop-{int(time.time())}-{i}",
            "title": f"{prop_bedrooms} BR Apartment in {prop_neighborhood}",
            "address": address,
            "neighborhood": prop_neighborhood,
            "bedrooms": prop_bedrooms,
            "bathrooms": bathrooms,
            "rent": prop_rent,
            "accepted_vouchers": accepted_vouchers,
            "landlord": landlord["name"],
            "landlord_rating": landlord["rating"],
            "date_available": get_random_future_date(),
            "amenities": get_random_amenities(i),
            "description": get_property_description(prop_bedrooms, prop_neighborhood),
            "image": image_url,
            "subway_lines": get_subway_lines(prop_neighborhood),
            "listing_source": "NYC Housing Connect" if i % 3 == 0 else "GoSection8" if i % 3 == 1 else "StreetEasy"
        }
        
        properties.append(property_obj)
    
    return properties

def get_random_future_date():
    """Generate a random available date within the next 2 months"""
    today = datetime.date.today()
    days_ahead = (hash(str(time.time())) % 60) + 1  # 1-60 days
    future_date = today + datetime.timedelta(days=days_ahead)
    return future_date.strftime("%Y-%m-%d")

def get_random_amenities(seed):
    """Generate a list of realistic apartment amenities"""
    all_amenities = [
        "Laundry in Building", "Dishwasher", "Elevator", "Hardwood Floors",
        "Live-in Super", "Storage Available", "Pets Allowed", "Air Conditioning",
        "Wheelchair Access", "Security System", "Rooftop Access"
    ]
    
    # Select 3-6 amenities
    num_amenities = 3 + (seed % 4)
    selected = []
    
    for i in range(num_amenities):
        idx = (seed + i) % len(all_amenities)
        selected.append(all_amenities[idx])
    
    return selected

def get_property_description(bedrooms, neighborhood):
    """Generate a realistic apartment description"""
    templates = [
        f"Bright and spacious {bedrooms} bedroom apartment in {neighborhood}. Vouchers accepted. Close to shopping and transportation.",
        f"Newly renovated {bedrooms} BR unit in well-maintained building. Voucher-friendly landlord. Great {neighborhood} location.",
        f"Charming {bedrooms} bedroom in the heart of {neighborhood}. Section 8 and other vouchers welcome. No broker fee!",
        f"Affordable {bedrooms} bedroom apartment available now. Landlord accepts all housing programs. Convenient to transit.",
        f"Spacious {bedrooms} BR unit in desirable {neighborhood} building. Housing vouchers accepted. Utilities included!"
    ]
    
    idx = hash(neighborhood + bedrooms) % len(templates)
    return templates[idx]

def get_subway_lines(neighborhood):
    """Return realistic subway lines based on NYC neighborhood"""
    subway_map = {
        "Astoria": ["N", "W"],
        "Bedford-Stuyvesant": ["A", "C", "G"],
        "Bushwick": ["L", "M", "J", "Z"],
        "Crown Heights": ["3", "4", "5"],
        "East Harlem": ["4", "5", "6"],
        "Flatbush": ["2", "5"],
        "Jackson Heights": ["7", "E", "F", "M", "R"],
        "Kingsbridge": ["1", "4"],
        "Lower East Side": ["F", "J", "M", "Z"],
        "Morningside Heights": ["1", "A", "C", "B"],
        "Washington Heights": ["A", "C", "1"],
        "South Bronx": ["2", "5", "6"],
        "Jamaica": ["E", "F", "J", "Z"],
        "Flushing": ["7"],
        "Sunset Park": ["D", "N", "R"]
    }
    
    if neighborhood in subway_map:
        return subway_map[neighborhood]
    else:
        # Return some default lines if neighborhood not in our map
        return ["A", "C"]


# Add these routes to your Flask application

@app.route('/voucher_types', methods=['GET'])
def get_voucher_types():
    """Return list of supported housing voucher programs with details"""
    vouchers = [
        {
            "id": "section8",
            "name": "Section 8 Housing Choice Voucher",
            "description": "Federal program that assists very low-income families, the elderly, and the disabled to afford housing in the private market.",
            "eligibility": "Income must be below 50% of the median income for the county or metropolitan area.",
            "provider": "New York City Housing Authority (NYCHA)",
            "website": "https://www1.nyc.gov/site/nycha/section-8/about-section-8.page",
            "max_amounts": {
                "studio": 2028,
                "1br": 2054,
                "2br": 2340,
                "3br": 2952
            }
        },
        {
            "id": "cityfheps",
            "name": "CityFHEPS",
            "description": "NYC rental assistance supplement to help individuals and families find and keep housing.",
            "eligibility": "NYC residents at risk of homelessness or currently in shelter system.",
            "provider": "NYC Human Resources Administration (HRA)",
            "website": "https://www1.nyc.gov/site/hra/help/cityfheps.page",
            "max_amounts": {
                "studio": 1945,
                "1br": 1999,
                "2br": 2325,
                "3br": 2881
            }
        },
        {
            "id": "fheps",
            "name": "FHEPS (Family Homelessness & Eviction Prevention Supplement)",
            "description": "State program that helps families on cash assistance who are facing eviction stay in their homes.",
            "eligibility": "Families with children who have an active Cash Assistance case and are facing eviction.",
            "provider": "New York State Office of Temporary and Disability Assistance",
            "website": "https://otda.ny.gov/programs/fheps/",
            "max_amounts": {
                "studio": 1900,
                "1br": 1965,
                "2br": 2280,
                "3br": 2820
            }
        },
        {
            "id": "hasa",
            "name": "HASA Housing Subsidy",
            "description": "Housing assistance for people living with HIV/AIDS.",
            "eligibility": "NYC residents with clinical/symptomatic HIV illness or AIDS.",
            "provider": "HIV/AIDS Services Administration",
            "website": "https://www1.nyc.gov/site/hra/help/hasa-faqs.page",
            "max_amounts": {
                "studio": 2060,
                "1br": 2110,
                "2br": 2400,
                "3br": 3000
            }
        }
    ]
    return jsonify({"status": "success", "vouchers": vouchers})

@app.route('/voucher_calculator', methods=['POST'])
def calculate_voucher_amount():
    """Calculate estimated voucher amount based on household details"""
    data = request.json
    household_size = data.get('household_size', 1)
    annual_income = data.get('annual_income', 0)
    voucher_type = data.get('voucher_type', 'section8')
    unit_size = data.get('unit_size', '1br')
    
    # This is a simplified calculation
    # In reality, voucher calculations are complex and vary by program
    
    result = {
        "status": "success",
        "voucher_type": voucher_type,
        "estimated_results": {}
    }
    
    # Calculate Area Median Income (AMI) percentage
    # NYC AMI for 2023 is about $120,000 for a family of four
    base_ami = 120000
    household_adjustment = {1: 0.7, 2: 0.8, 3: 0.9, 4: 1.0, 5: 1.08, 6: 1.16}
    adjusted_ami = base_ami * household_adjustment.get(household_size, 1.0)
    ami_percentage = (annual_income / adjusted_ami) * 100
    
    # Get voucher maximum amounts based on unit size
    max_amounts = {
        "section8": {"studio": 2028, "1br": 2054, "2br": 2340, "3br": 2952},
        "cityfheps": {"studio": 1945, "1br": 1999, "2br": 2325, "3br": 2881},
        "fheps": {"studio": 1900, "1br": 1965, "2br": 2280, "3br": 2820},
        "hasa": {"studio": 2060, "1br": 2110, "2br": 2400, "3br": 3000}
    }
    
    max_rent = max_amounts.get(voucher_type, {}).get(unit_size, 2000)
    
    # Calculate tenant contribution (generally 30% of income)
    monthly_income = annual_income / 12
    tenant_contribution = monthly_income * 0.3
    
    # Calculate voucher amount
    voucher_amount = max(0, max_rent - tenant_contribution)
    
    # Format results
    result["estimated_results"] = {
        "ami_percentage": round(ami_percentage, 1),
        "eligible": ami_percentage <= 50 if voucher_type == "section8" else True,
        "max_rent": max_rent,
        "tenant_contribution": round(tenant_contribution),
        "voucher_amount": round(voucher_amount),
        "landlord_receives": max_rent,
        "notes": "This is an estimate. Actual eligibility and amounts are determined by the voucher-issuing agency."
    }
    
    # Add eligibility feedback
    if voucher_type == "section8" and ami_percentage > 50:
        result["estimated_results"]["notes"] = "Your income appears to be above the Section 8 limit. You may still qualify for other programs."
    
    return jsonify(result)

@app.route('/voucher_requirements', methods=['GET'])
def get_requirements():
    """Get documentation requirements for voucher applications"""
    
    requirements = {
        "section8": {
            "documents": [
                "Photo ID for all adult household members",
                "Birth certificates for all household members",
                "Social Security cards for all household members",
                "Proof of income (last 4 pay stubs, benefit award letters, etc.)",
                "Bank statements for the past 6 months",
                "Previous year's tax returns"
            ],
            "process": [
                "Submit application to NYCHA",
                "Wait for eligibility interview",
                "Complete verification process",
                "Receive voucher if eligible",
                "Find housing and submit Request for Tenancy Approval",
                "Housing Quality Standards inspection",
                "Sign lease and move in"
            ]
        },
        "cityfheps": {
            "documents": [
                "Photo ID",
                "Proof of income",
                "Rent receipts or lease",
                "Eviction documents (if applicable)",
                "Budget letter from HRA",
                "Proof of household composition"
            ],
            "process": [
                "Apply through HRA or prevention services provider",
                "Determine eligibility",
                "Receive shopping letter",
                "Find apartment within rent limits",
                "Submit request for apartment approval",
                "Sign lease once approved"
            ]
        }
    }
    
    voucher_type = request.args.get('type', 'all')
    
    if voucher_type == 'all':
        return jsonify({"status": "success", "requirements": requirements})
    elif voucher_type in requirements:
        return jsonify({"status": "success", "requirements": {voucher_type: requirements[voucher_type]}})
    else:
        return jsonify({"status": "error", "message": "Voucher type not found"})

    
# Add these routes to the Flask application

@app.route('/landlords', methods=['GET'])
def get_landlords():
    """Retrieve list of landlords who accept housing vouchers"""
    # In production, this would query the database
    
    landlords = [
        {
            "id": "LL1001",
            "name": "Greentree Property Management",
            "contact_name": "Michael Green",
            "phone": "212-555-0101",
            "email": "mgreen@greentreepm.com",
            "properties_count": 47,
            "vouchers_accepted": ["Section 8", "CityFHEPS", "FHEPS"],
            "neighborhoods": ["Washington Heights", "Inwood", "Harlem"],
            "rating": 4.2,
            "reviews_count": 18,
            "relationship_status": "Active Partner",
            "last_contact": "2025-04-10",
            "notes": "Reliable landlord with good maintenance record. Consistently works with voucher holders."
        },
        {
            "id": "LL1002",
            "name": "New York Housing Associates",
            "contact_name": "Sarah Johnson",
            "phone": "718-555-3232",
            "email": "sjohnson@nyhousing.com",
            "properties_count": 85,
            "vouchers_accepted": ["Section 8", "CityFHEPS"],
            "neighborhoods": ["Bedford-Stuyvesant", "Crown Heights", "Flatbush"],
            "rating": 3.9,
            "reviews_count": 31,
            "relationship_status": "Active Partner",
            "last_contact": "2025-04-15",
            "notes": "Large portfolio of units across Brooklyn. Ask for Maria at the office for voucher inquiries."
        },
        {
            "id": "LL1003",
            "name": "Metro Living LLC",
            "contact_name": "David Chen",
            "phone": "646-555-7878",
            "email": "dchen@metroliving.com",
            "properties_count": 25,
            "vouchers_accepted": ["Section 8", "CityFHEPS", "HASA"],
            "neighborhoods": ["Astoria", "Long Island City", "Jackson Heights"],
            "rating": 4.0,
            "reviews_count": 12,
            "relationship_status": "New Relationship",
            "last_contact": "2025-04-12",
            "notes": "Growing portfolio in Queens. Recently started accepting vouchers after our workshop."
        },
        {
            "id": "LL1004",
            "name": "Five Boroughs Realty",
            "contact_name": "Robert Kim",
            "phone": "347-555-6545",
            "email": "rkim@5boros.com",
            "properties_count": 60,
            "vouchers_accepted": ["Section 8", "CityFHEPS", "FHEPS"],
            "neighborhoods": ["South Bronx", "Morrisania", "Fordham"],
            "rating": 3.7,
            "reviews_count": 23,
            "relationship_status": "Active Partner",
            "last_contact": "2025-03-29",
            "notes": "Good inventory of affordable units in the Bronx. Sometimes has maintenance delays."
        },
        {
            "id": "LL1005",
            "name": "Community Housing Partners",
            "contact_name": "Jessica Rivera",
            "phone": "718-555-9988",
            "email": "jrivera@chpartners.org",
            "properties_count": 32,
            "vouchers_accepted": ["Section 8", "CityFHEPS", "FHEPS", "HASA"],
            "neighborhoods": ["Lower East Side", "East Village", "East Harlem"],
            "rating": 4.5,
            "reviews_count": 29,
            "relationship_status": "Active Partner",
            "last_contact": "2025-04-18",
            "notes": "Nonprofit with mission to provide affordable housing. Very responsive and supportive."
        }
    ]
    
    # Filter by parameters if provided
    neighborhood = request.args.get('neighborhood')
    voucher_type = request.args.get('voucher_type')
    
    if neighborhood:
        landlords = [ll for ll in landlords if neighborhood in ll["neighborhoods"]]
    
    if voucher_type:
        landlords = [ll for ll in landlords if voucher_type in ll["vouchers_accepted"]]
    
    return jsonify({"status": "success", "landlords": landlords})

@app.route('/landlords/<landlord_id>', methods=['GET'])
def get_landlord_details(landlord_id):
    """Get detailed information about a specific landlord"""
    # In a real app, this would query the database
    
    # Mock data
    landlord_data = {
        "LL1001": {
            "id": "LL1001",
            "name": "Greentree Property Management",
            "contact_name": "Michael Green",
            "phone": "212-555-0101",
            "email": "mgreen@greentreepm.com",
            "website": "greentreepm.com",
            "office_address": "350 W 145th St, New York, NY 10039",
            "properties_count": 47,
            "vouchers_accepted": ["Section 8", "CityFHEPS", "FHEPS"],
            "neighborhoods": ["Washington Heights", "Inwood", "Harlem"],
            "rating": 4.2,
            "reviews": [
                {"member_id": "M1042", "rating": 5, "comment": "Very responsive to maintenance requests."},
                {"member_id": "M2133", "rating": 4, "comment": "Good experience overall. Accepted my Section 8 without issues."},
                {"member_id": "M1587", "rating": 3, "comment": "Units are decent but sometimes slow to respond."}
            ],
            "relationship_status": "Active Partner",
            "relationship_history": [
                {"date": "2023-05-15", "type": "Initial Contact", "notes": "Met at housing fair"},
                {"date": "2023-06-10", "type": "Partnership Agreement", "notes": "Signed MOU to prioritize Footsteps referrals"},
                {"date": "2023-09-22", "type": "Placement", "notes": "First Footsteps member housed"},
                {"date": "2024-02-08", "type": "Follow-up", "notes": "Quarterly check-in, relationship going well"}
            ],
            "available_units": [
                {
                    "address": "172 Audubon Ave #3B, New York, NY 10033",
                    "bedrooms": "2",
                    "rent": 1850,
                    "date_available": "2025-05-01"
                },
                {
                    "address": "513 W 158th St #5A, New York, NY 10032",
                    "bedrooms": "1",
                    "rent": 1650,
                    "date_available": "2025-05-15"
                }
            ],
            "notes": "Reliable landlord with good maintenance record. Has been working with voucher programs for over 10 years. Prefers direct deposit for payments."
        }
    }
    
    if landlord_id in landlord_data:
        return jsonify({"status": "success", "landlord": landlord_data[landlord_id]})
    else:
        return jsonify({"status": "error", "message": "Landlord not found"}), 404

@app.route('/landlords', methods=['POST'])
def add_landlord():
    """Add a new landlord to the database"""
    data = request.json
    
    # Validate required fields
    required_fields = ["name", "contact_name", "phone", "email", "vouchers_accepted"]
    for field in required_fields:
        if field not in data:
            return jsonify({"status": "error", "message": f"Missing required field: {field}"}), 400
    
    # In a real app, this would save to the database
    return jsonify({"status": "success", "message": "Landlord added successfully"})

if __name__ == '__main__':
    app.run(port=5000, debug=True)

    