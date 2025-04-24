from flask import Flask, jsonify, request
from concurrent.futures import ThreadPoolExecutor
import hashlib
import logging
import pandas as pd
from bs4 import BeautifulSoup
import requests
from urllib.parse import urlparse, parse_qs
import random
from datetime import datetime, timedelta
import threading
import json
import os
import re
import time

# Import selenium components
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from webdriver_manager.chrome import ChromeDriverManager
    selenium_available = True
except ImportError:
    selenium_available = False
    print("Selenium not available. Web scraping functionality will be limited.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("housing_navigator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("housing_navigator")

# Create a real database connection (using SQLAlchemy)
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, JSON, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///housing_navigator.db"  # Replace with PostgreSQL in production
engine = create_engine(DATABASE_URL)
Base = declarative_base()
Session = sessionmaker(bind=engine)

# Define database models
class Property(Base):
    __tablename__ = "properties"
    
    id = Column(String, primary_key=True)
    title = Column(String)
    address = Column(String)
    neighborhood = Column(String)
    bedrooms = Column(String)
    bathrooms = Column(String)
    rent = Column(Float)
    accepted_vouchers = Column(JSON)
    landlord = Column(String)
    landlord_id = Column(String)
    date_available = Column(String)
    amenities = Column(JSON)
    description = Column(Text)
    image_url = Column(String)
    subway_lines = Column(JSON)
    listing_source = Column(String)
    listing_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    active = Column(Boolean, default=True)
    
class UserProfile(Base):
    __tablename__ = "users"
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True)
    name = Column(String)
    preferences = Column(JSON)
    search_history = Column(JSON)
    saved_properties = Column(JSON)
    usage_count = Column(Integer, default=0)
    last_reset = Column(DateTime, default=datetime.utcnow)
    premium = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# Initialize database
Base.metadata.create_all(engine)

# Helper function to get subway lines for a neighborhood
def get_subway_lines(neighborhood):
    subway_data = {
        "Astoria": ["N", "W", "M", "R"],
        "Bedford-Stuyvesant": ["A", "C", "G", "J", "M", "Z"],
        "Bushwick": ["J", "M", "Z", "L"],
        "Crown Heights": ["2", "3", "4", "5", "S"],
        "East Harlem": ["4", "5", "6", "2", "3"],
        "Flatbush": ["2", "5", "Q"],
        "Washington Heights": ["1", "A", "C"],
        "South Bronx": ["4", "5", "6", "B", "D"],
        "Manhattan": ["1", "2", "3", "4", "5", "6", "A", "C", "E", "B", "D", "F", "M", "N", "Q", "R", "W", "J", "Z", "L", "G"],
        "Brooklyn": ["A", "C", "E", "F", "G", "J", "L", "M", "N", "Q", "R", "Z", "2", "3", "4", "5"],
        "Queens": ["E", "F", "M", "R", "N", "W", "7", "G"],
        "Bronx": ["1", "2", "4", "5", "6", "B", "D"],
        "Staten Island": ["SIR"]
    }
    
    return subway_data.get(neighborhood, ["Unknown"])

# Helper functions for property extraction
def extract_neighborhood(address):
    nyc_neighborhoods = [
        "Astoria", "Bedford-Stuyvesant", "Bushwick", "Crown Heights", "East Harlem",
        "Flatbush", "Jackson Heights", "Kingsbridge", "Lower East Side", "Morningside Heights",
        "Washington Heights", "South Bronx", "Jamaica", "Flushing", "Sunset Park", "Harlem",
        "East Village", "West Village", "Chelsea", "Midtown", "Financial District", "Brooklyn Heights",
        "Park Slope", "Williamsburg", "Greenpoint", "Long Island City", "Forest Hills", "Riverdale"
    ]
    
    for neighborhood in nyc_neighborhoods:
        if neighborhood in address:
            return neighborhood
    
    # Try to extract borough at minimum
    boroughs = ["Manhattan", "Brooklyn", "Queens", "Bronx", "Staten Island"]
    for borough in boroughs:
        if borough in address:
            return borough
    
    return "New York"  # Default

def extract_landlord_from_listing(title, address):
    # This would be enhanced with a database of known landlords
    # For now, we'll use a simplified approach
    landlords = [
        "Greentree Property Management", "New York Housing Associates", "Metro Living LLC",
        "Five Boroughs Realty", "Community Housing Partners"
    ]
    
    # Use a hash of the address to consistently assign the same landlord
    hash_value = hash(address) % len(landlords)
    return landlords[hash_value]

def extract_amenities_from_listing(text):
    common_amenities = [
        "Laundry", "Dishwasher", "Elevator", "Hardwood", "No Fee", "Doorman",
        "Gym", "Pets", "Parking", "Storage", "Balcony", "Roof"
    ]
    
    found_amenities = []
    text_lower = text.lower()
    
    for amenity in common_amenities:
        if amenity.lower() in text_lower:
            found_amenities.append(amenity)
    
    return found_amenities if found_amenities else ["Contact for details"]

# Function to generate sample data (for development without scraping)
def generate_sample_data(count=20):
    properties = []
    neighborhoods = ["Astoria", "Bedford-Stuyvesant", "Bushwick", "Crown Heights", "East Harlem", 
                    "Flatbush", "Washington Heights", "South Bronx"]
    voucher_types = [["Section 8"], ["CityFHEPS"], ["FHEPS"], ["HASA"], 
                     ["Section 8", "CityFHEPS"], ["Section 8", "FHEPS"], ["CityFHEPS", "HASA"]]
    
    for i in range(count):
        bedrooms = random.choice(["Studio", "1", "2", "3", "4+"])
        neighborhood = random.choice(neighborhoods)
        rent = random.randint(1200, 3000)
        accepted_vouchers = random.choice(voucher_types)
        
        title = f"{bedrooms} BR Apartment in {neighborhood}"
        address = f"{random.randint(1, 999)} {random.choice(['Main', 'Broadway', 'Park', 'Ocean', 'Bedford'])} {random.choice(['St', 'Ave', 'Blvd'])}, {neighborhood}, NY"
        
        property_id = hashlib.md5(f"{title}{address}{bedrooms}{rent}".encode()).hexdigest()
        
        properties.append({
            "id": property_id,
            "title": title,
            "address": address,
            "neighborhood": neighborhood,
            "bedrooms": bedrooms,
            "bathrooms": str(random.randint(1, 3)),
            "rent": rent,
            "accepted_vouchers": accepted_vouchers,
            "landlord": extract_landlord_from_listing(title, address),
            "date_available": (datetime.now() + timedelta(days=random.randint(0, 30))).strftime("%Y-%m-%d"),
            "amenities": random.sample(["Laundry", "Dishwasher", "Elevator", "Hardwood", "No Fee", "Doorman", 
                                      "Gym", "Pets", "Parking", "Storage", "Balcony", "Roof"], 
                                     k=random.randint(2, 5)),
            "description": f"Beautiful {bedrooms} bedroom apartment in {neighborhood}. Recently renovated with modern appliances.",
            "image_url": f"https://placehold.co/600x400/png?text=NYC+Apartment+{random.randint(100, 999)}",
            "subway_lines": get_subway_lines(neighborhood),
            "listing_source": random.choice(["NYC Housing Connect", "GoSection8", "StreetEasy"]),
            "listing_url": f"https://example.com/listing/{property_id}",
        })
    
    return properties

# Flask app setup
app = Flask(__name__)

# CORS support
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
    return response

# API Routes
@app.route('/properties', methods=['GET'])
def get_properties():
    """
    Get properties with filters
    Example: /properties?neighborhood=Astoria&bedrooms=2&max_rent=2000&voucher_types=Section 8,CityFHEPS
    """
    try:
        # Get query parameters
        neighborhood = request.args.get('neighborhood', 'All NYC')
        bedrooms = request.args.get('bedrooms', 'Any')
        max_rent = request.args.get('max_rent', 3000)
        voucher_types = request.args.get('voucher_types', '').split(',')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
        
        # Using sample data for now since we're not actually scraping
        all_properties = generate_sample_data(50)
        
        # Apply filters
        filtered_properties = []
        for prop in all_properties:
            # Filter by neighborhood
            if neighborhood != 'All NYC' and prop['neighborhood'] != neighborhood:
                continue
                
            # Filter by bedrooms
            if bedrooms != 'Any':
                if bedrooms == '3+' and prop['bedrooms'] not in ['3', '4+']:
                    continue
                elif bedrooms != '3+' and prop['bedrooms'] != bedrooms:
                    continue
                    
            # Filter by max rent
            if int(prop['rent']) > int(max_rent):
                continue
                
            # Filter by voucher types
            if voucher_types and voucher_types[0]:  # Check if not empty list
                if not any(voucher in prop['accepted_vouchers'] for voucher in voucher_types):
                    continue
                    
            filtered_properties.append(prop)
        
        # Calculate pagination
        total_results = len(filtered_properties)
        total_pages = (total_results + per_page - 1) // per_page  # Ceiling division
        
        # Get current page results
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        current_page_results = filtered_properties[start_idx:end_idx]
        
        return jsonify({
            'status': 'success',
            'properties': current_page_results,
            'total_results': total_results,
            'page': page,
            'per_page': per_page,
            'total_pages': total_pages
        })
        
    except Exception as e:
        logger.error(f"Error in get_properties: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while retrieving properties'
        }), 500

@app.route('/properties/<property_id>', methods=['GET'])
def get_property_details(property_id):
    """Get detailed information about a specific property"""
    try:
        # In a real app, we'd query the database
        # For now, generate some sample data
        all_properties = generate_sample_data(50)
        
        # Find the property by ID
        property_data = next((p for p in all_properties if p['id'] == property_id), None)
        
        if property_data:
            # Add some additional details that wouldn't normally be in the list view
            property_data['description'] = "This beautiful apartment features hardwood floors throughout, high ceilings, and ample natural light. The kitchen has been recently renovated with stainless steel appliances and granite countertops. Building amenities include laundry in basement, live-in super, and a lovely courtyard. Heat and hot water included. Close to multiple subway lines and shopping."
            property_data['contact_info'] = {
                'name': 'Property Manager',
                'phone': '(212) 555-1234',
                'email': 'manager@example.com'
            }
            property_data['floor_plan'] = "1BR with living room, kitchen, bathroom"
            
            return jsonify({
                'status': 'success',
                'property': property_data
            })
        else:
            return jsonify({
                'status': 'error',
                'message': 'Property not found'
            }), 404
            
    except Exception as e:
        logger.error(f"Error in get_property_details: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while retrieving property details'
        }), 500

@app.route('/properties/recommended', methods=['GET'])
def get_recommended_properties():
    """Get personalized property recommendations for a user"""
    try:
        user_id = request.args.get('user_id')
        limit = int(request.args.get('limit', 10))
        
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'User ID is required'
            }), 400
            
        # Check if user exists and has premium status
        # In a real app, query the database
        # For now, we'll simulate it
        is_premium = random.choice([True, False])
        remaining_searches = 10 if not is_premium else None
        
        # Generate some recommendations
        all_properties = generate_sample_data(50)
        recommended = random.sample(all_properties, min(limit, len(all_properties)))
        
        # Add a relevance score to each property
        for prop in recommended:
            prop['relevance_score'] = random.randint(70, 99)
            
        # Sort by relevance score
        recommended.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        return jsonify({
            'status': 'success',
            'properties': recommended,
            'remaining_searches': remaining_searches
        })
        
    except Exception as e:
        logger.error(f"Error in get_recommended_properties: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while retrieving recommendations'
        }), 500

@app.route('/user/saved_properties', methods=['GET', 'POST'])
def saved_properties():
    """Get or save properties for a user"""
    try:
        user_id = request.args.get('user_id') or (request.json and request.json.get('user_id'))
        
        if not user_id:
            return jsonify({
                'status': 'error',
                'message': 'User ID is required'
            }), 400
            
        if request.method == 'GET':
            # Get user's saved properties
            # In a real app, query the database
            # For now, generate some sample data
            saved = generate_sample_data(random.randint(0, 5))
            
            return jsonify({
                'status': 'success',
                'saved_properties': saved
            })
            
        elif request.method == 'POST':
            # Save a property for a user
            property_id = request.json.get('property_id')
            
            if not property_id:
                return jsonify({
                    'status': 'error',
                    'message': 'Property ID is required'
                }), 400
                
            # In a real app, save to database
            # For now, just return success
            return jsonify({
                'status': 'success',
                'message': 'Property saved'
            })
            
    except Exception as e:
        logger.error(f"Error in saved_properties: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred processing the request'
        }), 500

@app.route('/properties/contact', methods=['POST'])
def contact_property():
    """Send a contact request for a property"""
    try:
        data = request.json
        user_id = data.get('user_id')
        property_id = data.get('property_id')
        
        if not user_id or not property_id:
            return jsonify({
                'status': 'error',
                'message': 'User ID and Property ID are required'
            }), 400
            
        # In a real app, save contact request to database and send email
        # For now, just return success
        return jsonify({
            'status': 'success',
            'message': 'Contact request sent'
        })
        
    except Exception as e:
        logger.error(f"Error in contact_property: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while sending the contact request'
        }), 500

@app.route('/auth/register', methods=['POST'])
def register_user():
    """Register a new user"""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        name = data.get('name')
        
        if not email or not password:
            return jsonify({
                'status': 'error',
                'message': 'Email and password are required'
            }), 400
            
        # In a real app, check if email already exists, hash password, create user
        # For now, just return success with a fake user ID
        user_id = hashlib.md5(email.encode()).hexdigest()
        
        return jsonify({
            'status': 'success',
            'message': 'User registered successfully',
            'user_id': user_id
        })
        
    except Exception as e:
        logger.error(f"Error in register_user: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while registering the user'
        }), 500

@app.route('/analytics/track', methods=['POST'])
def track_analytics():
    """Track user analytics events"""
    try:
        data = request.json
        
        # In a real app, save analytics to database
        # For now, just log it
        logger.info(f"Analytics event: {data}")
        
        return jsonify({
            'status': 'success'
        })
        
    except Exception as e:
        logger.error(f"Error in track_analytics: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': 'An error occurred while tracking analytics'
        }), 500

# Startup message
@app.route('/')
def index():
    return jsonify({
        'status': 'success',
        'message': 'Housing Navigator API is running',
        'version': '1.0.0',
        'endpoints': [
            '/properties',
            '/properties/<property_id>',
            '/properties/recommended',
            '/user/saved_properties',
            '/properties/contact',
            '/auth/register',
            '/analytics/track'
        ]
    })

if __name__ == '__main__':
    print("Starting Housing Navigator API server...")
    print(f"Database will be stored at: {os.path.abspath('housing_navigator.db')}")
    
    if not selenium_available:
        print("WARNING: Selenium is not available. Live web scraping is disabled.")
        print("The API will use sample data instead.")
    
    print("\nAPI is running at http://127.0.0.1:5000/")
    print("Press CTRL+C to quit")
    
    app.run(debug=True)