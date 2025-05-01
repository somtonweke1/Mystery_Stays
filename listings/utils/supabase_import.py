import pandas as pd
from ..supabase_config import (
    supabase,
    supabase_service,
    PROPERTIES_TABLE,
    IMAGES_TABLE,
    AMENITIES_TABLE,
    PROPERTY_AMENITIES_TABLE,
    LOCATIONS_TABLE,
    LANDLORDS_TABLE,
    BOOKINGS_TABLE
)

def import_properties_from_csv(csv_path):
    """
    Import properties from a CSV file to Supabase.
    CSV should have the following columns:
    - title
    - description
    - property_type
    - bedrooms
    - bathrooms
    - rent_amount
    - is_available
    - rating
    - landlord_name
    - landlord_email
    - city
    - state
    - address
    - amenities (comma-separated)
    - image_urls (comma-separated)
    """
    try:
        # Read CSV file
        df = pd.read_csv(csv_path)
        
        # Process each row
        for _, row in df.iterrows():
            # 1. Create or get landlord
            landlord_data = {
                "name": row["landlord_name"],
                "email": row["landlord_email"]
            }
            landlord = supabase.table(LANDLORDS_TABLE).upsert(landlord_data).execute()
            landlord_id = landlord.data[0]["id"]
            
            # 2. Create or get location
            location_data = {
                "city": row["city"],
                "state": row["state"],
                "address": row["address"]
            }
            location = supabase.table(LOCATIONS_TABLE).upsert(location_data).execute()
            location_id = location.data[0]["id"]
            
            # 3. Create property
            property_data = {
                "title": row["title"],
                "description": row["description"],
                "property_type": row["property_type"],
                "bedrooms": row["bedrooms"],
                "bathrooms": row["bathrooms"],
                "rent_amount": row["rent_amount"],
                "is_available": row["is_available"],
                "rating": row["rating"],
                "landlord_id": landlord_id,
                "location_id": location_id
            }
            property = supabase.table(PROPERTIES_TABLE).insert(property_data).execute()
            property_id = property.data[0]["id"]
            
            # 4. Add amenities
            amenities = [a.strip() for a in row["amenities"].split(",")]
            for amenity_name in amenities:
                # Create or get amenity
                amenity = supabase.table(AMENITIES_TABLE).upsert({"name": amenity_name}).execute()
                amenity_id = amenity.data[0]["id"]
                
                # Link property to amenity
                supabase.table(PROPERTY_AMENITIES_TABLE).insert({
                    "property_id": property_id,
                    "amenity_id": amenity_id
                }).execute()
            
            # 5. Add images
            image_urls = [url.strip() for url in row["image_urls"].split(",")]
            for url in image_urls:
                supabase.table(IMAGES_TABLE).insert({
                    "property_id": property_id,
                    "image_url": url
                }).execute()
        
        return True, "Properties imported successfully"
    
    except Exception as e:
        return False, f"Error importing properties: {str(e)}"

def import_bookings_from_csv(csv_path):
    """
    Import bookings from a CSV file to Supabase.
    CSV should have the following columns:
    - property_id
    - user_id
    - check_in
    - check_out
    - guests
    - total_price
    - status
    """
    try:
        # Read CSV file
        df = pd.read_csv(csv_path)
        
        # Process each row
        for _, row in df.iterrows():
            booking_data = {
                "property_id": row["property_id"],
                "user_id": row["user_id"],
                "check_in": row["check_in"],
                "check_out": row["check_out"],
                "guests": row["guests"],
                "total_price": row["total_price"],
                "status": row["status"]
            }
            supabase.table(BOOKINGS_TABLE).insert(booking_data).execute()
        
        return True, "Bookings imported successfully"
    
    except Exception as e:
        return False, f"Error importing bookings: {str(e)}" 