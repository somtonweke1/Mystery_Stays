import requests
BASE = "http://127.0.0.1:5000"  # Base URL for the Housing Navigator API

# Search for properties based on criteria
resp = requests.get(f"{BASE}/properties", params={
    "neighborhood": "Bedford-Stuyvesant",
    "max_rent": 2000,
    "min_bedrooms": 2,
    "voucher_type": "Section 8"
})
print("Property search results:", resp.json())

# Get personalized property recommendations for a user
resp = requests.get(f"{BASE}/properties/recommended", params={
    "user_id": "user123",
    "limit": 10
})
print("Recommended properties:", resp.json())

# Register a new user
resp = requests.post(f"{BASE}/auth/register", json={
    "email": "user@example.com",
    "password": "securepassword",
    "name": "Jane Doe"
})
print("User registration:", resp.json())

# Update user preferences
resp = requests.post(f"{BASE}/user/preferences", json={
    "user_id": "user123",
    "preferences": {
        "neighborhoods": ["Bedford-Stuyvesant", "Crown Heights"],
        "max_rent": 2000,
        "bedrooms": 2,
        "voucher_types": ["Section 8", "CityFHEPS"],
        "preferred_features": ["laundry", "dishwasher"],
        "preferred_locations": [[40.6872, -73.9418]]  # Example coordinates in Bed-Stuy
    }
})
print("Update preferences:", resp.json())

# Save a property to user's favorites
resp = requests.post(f"{BASE}/user/saved_properties", json={
    "user_id": "user123",
    "property_id": "prop456"
})
print("Save property:", resp.json())

# Get user's saved properties
resp = requests.get(f"{BASE}/user/saved_properties", params={
    "user_id": "user123"
})
print("Saved properties:", resp.json())

# Get available neighborhoods
resp = requests.get(f"{BASE}/neighborhoods")
print("Neighborhoods:", resp.json())

# Get property details
resp = requests.get(f"{BASE}/properties/prop456")
print("Property details:", resp.json())

# Admin: Add new property
resp = requests.post(f"{BASE}/admin/properties", json={
    "title": "Spacious 2BR in Bed-Stuy",
    "address": "123 Malcolm X Blvd, Brooklyn, NY 11221",
    "neighborhood": "Bedford-Stuyvesant",
    "coordinates": [40.6872, -73.9418],
    "bedrooms": 2,
    "bathrooms": 1,
    "rent": 1900,
    "deposit": 1900,
    "accepted_vouchers": ["Section 8", "CityFHEPS"],
    "features": ["laundry", "dishwasher", "hardwood floors"],
    "description": "Beautiful apartment with lots of natural light",
    "landlord": "Sunshine Properties",
    "image_url": "https://example.com/image.jpg",
    "listing_source": "StreetEasy",
    "available_date": "2025-05-01T00:00:00"
})
print("Add property:", resp.json())

# Admin: Update a property
resp = requests.put(f"{BASE}/admin/properties/prop456", json={
    "rent": 1950,
    "description": "Updated description with new amenities"
})
print("Update property:", resp.json())

# Admin: Deactivate a property
resp = requests.post(f"{BASE}/admin/properties/prop456/deactivate")
print("Deactivate property:", resp.json())