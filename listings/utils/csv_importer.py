import pandas as pd
import re
from ..models import Property, Landlord, Location, Amenity, PropertyAmenity
from django.utils.text import slugify

def import_properties_from_csv(csv_path):
    """
    Import properties directly into Django database from CSV.
    """
    try:
        # Read CSV file
        df = pd.read_csv(csv_path)
        properties_created = 0
        
        # Default amenities
        default_amenities = ['WiFi', 'Kitchen']
        amenity_objects = {}
        for amenity_name in default_amenities:
            amenity_objects[amenity_name] = Amenity.objects.get_or_create(name=amenity_name)[0]
        
        for _, row in df.iterrows():
            try:
                # 1. Create or get landlord
                landlord_name = str(row["Poster's Name"])
                landlord_email = str(row['Email Address'])
                landlord = Landlord.objects.get_or_create(
                    name=landlord_name,
                    email=landlord_email
                )[0]
                
                # 2. Create or get location
                location_str = str(row['Housing Location'])
                location_parts = location_str.split(',')
                city = location_parts[0].strip()
                state = location_parts[1].strip() if len(location_parts) > 1 else 'Unknown'
                
                location = Location.objects.get_or_create(
                    city=city,
                    state=state,
                    country='USA',  # Default to USA
                    address=location_str
                )[0]
                
                # 3. Process rent amount
                rent_str = str(row['What is the cost of rent?'])
                numbers = re.findall(r'\d+', rent_str)
                rent_amount = float(numbers[0]) if numbers else 0.0
                
                # 4. Create property
                title = str(row['Post headline '])
                description = str(row['Housing post text'])
                
                # Generate a unique listing_id
                listing_id = f"AVODAH-{slugify(title)[:30]}"
                
                property = Property.objects.create(
                    listing_id=listing_id,
                    title=title,
                    description=description,
                    landlord=landlord,
                    location=location,
                    property_type='APARTMENT',  # Default to apartment
                    bedrooms=1,  # Default
                    bathrooms=1,  # Default
                    rent_amount=rent_amount,
                    rating=5,  # Default rating
                    is_available=True,
                    source='OTHER'
                )
                
                # 5. Add amenities
                for amenity in amenity_objects.values():
                    PropertyAmenity.objects.create(
                        property=property,
                        amenity=amenity
                    )
                
                properties_created += 1
                
            except Exception as e:
                print(f"Error processing row: {row}")
                print(f"Error details: {str(e)}")
                continue
        
        return True, f"Successfully imported {properties_created} properties"
        
    except Exception as e:
        return False, f"Error importing properties: {str(e)}" 