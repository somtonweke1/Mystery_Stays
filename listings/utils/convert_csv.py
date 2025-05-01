import pandas as pd
import re

def convert_avodah_csv(input_file, output_file):
    """
    Convert Avodah CSV format to our property listing format.
    """
    # Read the input CSV
    df = pd.read_csv(input_file)
    
    # Create a new DataFrame with our required columns
    converted_data = []
    
    for _, row in df.iterrows():
        try:
            # Extract basic information
            title = str(row['Post headline '])
            description = str(row['Housing post text'])
            
            # Handle rent amount
            rent_str = str(row['What is the cost of rent?'])
            # Extract numbers from the string
            numbers = re.findall(r'\d+', rent_str)
            if numbers:
                rent_amount = float(numbers[0])
            else:
                rent_amount = 0.0
                
            landlord_name = str(row["Poster's Name"])
            landlord_email = str(row['Email Address'])
            
            # Extract location information
            location = str(row['Housing Location'])
            # Try to split city and state
            location_parts = location.split(',')
            city = location_parts[0].strip()
            state = location_parts[1].strip() if len(location_parts) > 1 else ''
            
            # Create property entry
            property_data = {
                'title': title,
                'description': description,
                'property_type': 'APARTMENT',  # Default to apartment, can be modified
                'bedrooms': 1,  # Default to 1, can be modified
                'bathrooms': 1,  # Default to 1, can be modified
                'rent_amount': rent_amount,
                'is_available': True,
                'rating': 5,  # Default to 5, can be modified
                'landlord_name': landlord_name,
                'landlord_email': landlord_email,
                'city': city,
                'state': state,
                'address': location,
                'amenities': 'WiFi,Kitchen',  # Default amenities, can be modified
                'image_urls': ''  # No images in original data
            }
            
            converted_data.append(property_data)
        except Exception as e:
            print(f"Error processing row: {row}")
            print(f"Error details: {str(e)}")
            continue
    
    # Create new DataFrame
    converted_df = pd.DataFrame(converted_data)
    
    # Save to new CSV
    converted_df.to_csv(output_file, index=False)
    return output_file 