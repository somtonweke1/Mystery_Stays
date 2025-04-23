from flask import Flask, request, jsonify
from flask_cors import CORS
import datetime
from typing import List, Dict, Any
import os
import json
import time

# Create the Flask app
app = Flask(__name__)
CORS(app)

# Create directory for data storage if it doesn't exist
os.makedirs('data', exist_ok=True)

class MysteryStayAgent:
    def __init__(self):
        self.available_properties = []
        self.user_preferences = {}
        self.booked_stays = {}

    def add_available_property(self, property_details: Dict[str, Any]) -> str:
        """Add a vacant property to the pool at a 50% discount."""
        property_id = f"prop_{len(self.available_properties) + 1}"
        property_details = property_details.copy()
        property_details["id"] = property_id
        property_details["discount_price"] = property_details["original_price"] * 0.5
        self.available_properties.append(property_details)
        return property_id

    def register_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> None:
        """Register a digital nomad's preferences."""
        self.user_preferences[user_id] = preferences

    def match_user_to_properties(self, user_id: str) -> List[Dict[str, Any]]:
        """Find properties matching user preferences, hiding exact location."""
        if user_id not in self.user_preferences:
            return []
        preferences = self.user_preferences[user_id]
        matched = []
        for prop in self.available_properties:
            matches = True
            for key in preferences:
                if key == "location":
                    continue  # Hide location for mystery stays
                if key == "price_max" and prop["discount_price"] > preferences[key]:
                    matches = False
                elif key == "amenities" and not all(a in prop.get("amenities", []) for a in preferences[key]):
                    matches = False
                elif key not in ["price_max", "amenities"] and preferences[key] != prop.get(key):
                    matches = False
            if matches:
                # Hide exact location, show region
                mystery_prop = prop.copy()
                if "address" in mystery_prop:
                    del mystery_prop["address"]
                if "location" in mystery_prop:
                    mystery_prop["region"] = self._get_region(mystery_prop["location"])
                    del mystery_prop["location"]
                matched.append(mystery_prop)
        return matched

    def book_mystery_stay(self, user_id: str, property_id: str, check_in: datetime.date, check_out: datetime.date) -> Dict[str, Any]:
        """Book a mystery stay and return confirmation (location hidden)."""
        property_details = next((p for p in self.available_properties if p["id"] == property_id), None)
        if not property_details:
            return {"status": "failed", "reason": "Property not found"}
        booking_id = f"book_{len(self.booked_stays) + 1}"
        nights = (check_out - check_in).days
        booking = {
            "booking_id": booking_id,
            "user_id": user_id,
            "property_id": property_id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "total_price": property_details["discount_price"] * nights,
            "status": "confirmed",
            "property_details": property_details
        }
        self.booked_stays[booking_id] = booking
        confirmation = booking.copy()
        confirmation["property_details"] = self._get_limited_property_details(property_details)
        return confirmation

    def reveal_location(self, booking_id: str) -> Dict[str, Any]:
        """Reveal the exact location of a booked mystery stay."""
        booking = self.booked_stays.get(booking_id)
        if not booking:
            return {"status": "failed", "reason": "Booking not found"}
        return booking["property_details"]

    def _get_region(self, location: Dict[str, Any]) -> str:
        """Extract region info from location."""
        return f"{location.get('city', 'Unknown City')}, {location.get('country', 'Unknown Country')}"

    def _get_limited_property_details(self, property_details: Dict[str, Any]) -> Dict[str, Any]:
        """Hide location details, show only region."""
        limited = property_details.copy()
        for key in ["address", "location", "coordinates", "directions"]:
            if key in limited:
                del limited[key]
        if "location" in property_details:
            limited["region"] = self._get_region(property_details["location"])
        return limited

# Initialize the Mystery Stay Agent
mystery_agent = MysteryStayAgent()

# Sample data generator
def generate_sample_properties():
    """Generate sample properties for the mystery stay agent"""
    property_types = ["Apartment", "Villa", "Cottage", "Penthouse", "Loft"]
    cities = [
        {"city": "Lisbon", "country": "Portugal"},
        {"city": "Barcelona", "country": "Spain"},
        {"city": "Bali", "country": "Indonesia"},
        {"city": "Chiang Mai", "country": "Thailand"},
        {"city": "Mexico City", "country": "Mexico"},
        {"city": "Medellín", "country": "Colombia"},
        {"city": "Porto", "country": "Portugal"},
        {"city": "Berlin", "country": "Germany"}
    ]
    
    amenities_options = [
        ["WiFi", "Kitchen", "Workspace", "Air Conditioning"],
        ["WiFi", "Kitchen", "Pool", "Workspace", "Gym"],
        ["WiFi", "Workspace", "Beachfront", "Kitchen"],
        ["WiFi", "Coworking Space", "Laundry", "Kitchen"],
        ["WiFi", "Mountain View", "Kitchen", "Heating"]
    ]
    
    properties = []
    for i in range(20):
        city_idx = i % len(cities)
        prop_type_idx = i % len(property_types)
        amenities_idx = i % len(amenities_options)
        
        property_details = {
            "name": f"{property_types[prop_type_idx]} in {cities[city_idx]['city']}",
            "type": property_types[prop_type_idx],
            "location": cities[city_idx],
            "original_price": 1000 + (i * 100),
            "bedrooms": (i % 3) + 1,
            "bathrooms": (i % 2) + 1,
            "max_guests": ((i % 3) + 1) * 2,
            "amenities": amenities_options[amenities_idx],
            "address": f"{100 + i} Example Street, {cities[city_idx]['city']}",
            "coordinates": {"lat": 0, "lng": 0},  # Would be real coordinates in production
            "rating": round(3.5 + (i % 5) * 0.3, 1),
            "reviews_count": i * 5,
            "image_url": f"https://example.com/property_{i}.jpg"
        }
        mystery_agent.add_available_property(property_details)

# Generate sample properties on startup
generate_sample_properties()

# Root route
@app.route("/")
def home():
    return "Mystery Stay API is running!"

@app.route('/properties', methods=['GET'])
def get_properties():
    """Get all properties (only showing region, not exact location)"""
    properties = []
    for prop in mystery_agent.available_properties:
        limited_prop = mystery_agent._get_limited_property_details(prop)
        properties.append(limited_prop)
    
    return jsonify({
        "status": "success",
        "count": len(properties),
        "properties": properties
    })

@app.route('/users/<user_id>/preferences', methods=['POST'])
def set_user_preferences(user_id):
    """Register a user's stay preferences"""
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
    
    mystery_agent.register_user_preferences(user_id, data)
    
    return jsonify({
        "status": "success",
        "message": f"Preferences for user {user_id} registered successfully"
    })

@app.route('/users/<user_id>/matches', methods=['GET'])
def get_user_matches(user_id):
    """Get properties matching user preferences"""
    matched_properties = mystery_agent.match_user_to_properties(user_id)
    
    return jsonify({
        "status": "success",
        "count": len(matched_properties),
        "properties": matched_properties
    })

@app.route('/bookings', methods=['POST'])
def create_booking():
    """Book a mystery stay"""
    data = request.json
    if not data:
        return jsonify({"status": "error", "message": "No data provided"}), 400
    
    required_fields = ["user_id", "property_id", "check_in", "check_out"]
    for field in required_fields:
        if field not in data:
            return jsonify({"status": "error", "message": f"Missing required field: {field}"}), 400
    
    try:
        check_in = datetime.date.fromisoformat(data["check_in"])
        check_out = datetime.date.fromisoformat(data["check_out"])
    except ValueError:
        return jsonify({"status": "error", "message": "Invalid date format. Use YYYY-MM-DD"}), 400
    
    result = mystery_agent.book_mystery_stay(
        data["user_id"],
        data["property_id"],
        check_in,
        check_out
    )
    
    if result["status"] == "failed":
        return jsonify({"status": "error", "message": result["reason"]}), 400
    
    return jsonify({
        "status": "success",
        "booking": result
    })

@app.route('/bookings/<booking_id>/reveal', methods=['GET'])
def reveal_location(booking_id):
    """Reveal the exact location of a mystery stay after booking"""
    result = mystery_agent.reveal_location(booking_id)
    
    if "status" in result and result["status"] == "failed":
        return jsonify({"status": "error", "message": result["reason"]}), 404
    
    return jsonify({
        "status": "success",
        "property_details": result
    })

@app.route('/property_types', methods=['GET'])
def get_property_types():
    """Get list of property types"""
    types = [
        {"id": "apartment", "name": "Apartment"},
        {"id": "villa", "name": "Villa"},
        {"id": "cottage", "name": "Cottage"},
        {"id": "penthouse", "name": "Penthouse"},
        {"id": "loft", "name": "Loft"}
    ]
    
    return jsonify({
        "status": "success",
        "property_types": types
    })

@app.route('/regions', methods=['GET'])
def get_regions():
    """Get list of available regions"""
    regions = []
    for prop in mystery_agent.available_properties:
        if "location" in prop:
            region = mystery_agent._get_region(prop["location"])
            if region not in regions:
                regions.append(region)
    
    return jsonify({
        "status": "success",
        "regions": regions
    })

if __name__ == '__main__':
    app.run(port=5000, debug=True)