import requests

BASE = "http://127.0.0.1:5000"  # Base URL for the Housing Navigator API

# Scan for housing options
resp = requests.post(f"{BASE}/scan_housing", json={
    "neighborhood": "Bedford-Stuyvesant",
    "max_rent": 2000,
    "bedrooms": "2",
    "voucher_types": ["Section 8", "CityFHEPS"]
})
print("Scan housing results:", resp.json())

# Get available voucher types
resp = requests.get(f"{BASE}/voucher_types")
print("Voucher types:", resp.json())

# Calculate voucher amount
resp = requests.post(f"{BASE}/voucher_calculator", json={
    "household_size": 3,
    "annual_income": 35000,
    "voucher_type": "section8",
    "unit_size": "2br"
})
print("Voucher calculation:", resp.json())

# Get voucher requirements
resp = requests.get(f"{BASE}/voucher_requirements?type=section8")
print("Voucher requirements:", resp.json())

# Get landlords who accept vouchers
resp = requests.get(f"{BASE}/landlords?neighborhood=Washington Heights&voucher_type=Section 8")
print("Landlords:", resp.json())

# Get detailed information about a specific landlord
resp = requests.get(f"{BASE}/landlords/LL1001")
print("Landlord details:", resp.json())

# Add a new landlord
resp = requests.post(f"{BASE}/landlords", json={
    "name": "Sunshine Properties",
    "contact_name": "Maria Rodriguez",
    "phone": "718-555-4321",
    "email": "mrodriguez@sunshine.com",
    "vouchers_accepted": ["Section 8", "CityFHEPS"],
    "neighborhoods": ["Astoria", "Long Island City"],
    "notes": "New landlord interested in working with voucher holders"
})
print("Add landlord:", resp.json())