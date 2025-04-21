import requests

BASE = "http://127.0.0.1:5001"  # Removed the square brackets

# Add a property
resp = requests.post(f"{BASE}/properties/add", json={
    "name": "Cozy Studio",
    "original_price": 100,
    "amenities": ["wifi", "kitchen"],
    "bedrooms": 1,
    "location": {"city": "Barcelona", "country": "Spain"}
})
print("Add property:", resp.json())

# Register user preferences
resp = requests.post(f"{BASE}/users/preferences", json={
    "user_id": "user1",
    "preferences": {
        "amenities": ["wifi", "kitchen"],
        "price_max": 80,
        "bedrooms": 1
    }
})
print("Register preferences:", resp.json())

# Get matches
resp = requests.get(f"{BASE}/properties/match/user1")
print("Matches:", resp.json())

# Book a stay
resp = requests.post(f"{BASE}/bookings/create", json={
    "user_id": "user1",
    "property_id": "prop_1",
    "check_in": "2025-05-01",
    "check_out": "2025-05-05"
})
print("Booking:", resp.json())

# Reveal location
resp = requests.get(f"{BASE}/bookings/reveal/book_1")
print("Reveal location:", resp.json())