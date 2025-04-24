# data_cleansing.py
import logging
import re
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import Property, engine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("data_cleansing.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def clean_price(price_str):
    """Convert price string to float value."""
    if not price_str or not isinstance(price_str, str):
        return None
    
    # Remove currency symbols, commas, and other non-numeric characters
    clean_str = re.sub(r'[^\d.]', '', price_str)
    try:
        return float(clean_str) if clean_str else None
    except ValueError:
        logger.warning(f"Could not convert price: {price_str}")
        return None

def clean_date(date_str):
    """Convert various date formats to YYYY-MM-DD."""
    if not date_str or not isinstance(date_str, str):
        return None
    
    date_formats = [
        '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', 
        '%d-%m-%Y', '%m-%d-%Y', '%d.%m.%Y'
    ]
    
    for date_format in date_formats:
        try:
            return datetime.strptime(date_str.strip(), date_format).strftime('%Y-%m-%d')
        except ValueError:
            continue
    
    logger.warning(f"Could not parse date: {date_str}")
    return None

def clean_area(area_str):
    """Convert area string to float value in square meters."""
    if not area_str or not isinstance(area_str, str):
        return None
    
    # Extract numeric value
    match = re.search(r'(\d+\.?\d*)', area_str)
    if not match:
        return None
    
    value = float(match.group(1))
    
    # Convert to square meters if needed
    if 'sq ft' in area_str.lower() or 'sqft' in area_str.lower():
        value *= 0.092903  # Convert sq ft to sq m
    
    return round(value, 2)

def validate_property(prop_data):
    """Validate property data and return clean version or None if invalid."""
    required_fields = ['address', 'price']
    
    # Check required fields
    for field in required_fields:
        if field not in prop_data or not prop_data[field]:
            logger.warning(f"Missing required field: {field}")
            return None
    
    # Validate price range
    if prop_data.get('price') and (prop_data['price'] <= 0 or prop_data['price'] > 100000000):
        logger.warning(f"Price out of realistic range: {prop_data['price']}")
        return None
    
    # Validate area
    if prop_data.get('area') and (prop_data['area'] <= 0 or prop_data['area'] > 10000):
        logger.warning(f"Area out of realistic range: {prop_data['area']}")
        return None
    
    return prop_data

def clean_dataframe(df):
    """Clean the entire dataframe of property listings."""
    logger.info(f"Starting data cleaning for {len(df)} records")
    
    # Make a copy to avoid modifying the original
    clean_df = df.copy()
    
    # Clean individual columns
    if 'price' in clean_df.columns:
        clean_df['price'] = clean_df['price'].apply(clean_price)
    
    if 'date_listed' in clean_df.columns:
        clean_df['date_listed'] = clean_df['date_listed'].apply(clean_date)
    
    if 'area' in clean_df.columns:
        clean_df['area'] = clean_df['area'].apply(clean_area)
    
    # Remove duplicates
    initial_count = len(clean_df)
    clean_df = clean_df.drop_duplicates(subset=['address', 'price'], keep='first')
    logger.info(f"Removed {initial_count - len(clean_df)} duplicate records")
    
    # Handle missing values
    for col in clean_df.columns:
        missing_count = clean_df[col].isna().sum()
        if missing_count > 0:
            logger.info(f"Column '{col}' has {missing_count} missing values")
    
    # Optional: Drop rows with missing critical data
    clean_df = clean_df.dropna(subset=['address', 'price'])
    
    # Filter out invalid data
    clean_df = clean_df[clean_df['price'] > 0]
    if 'area' in clean_df.columns:
        clean_df = clean_df[clean_df['area'].isna() | (clean_df['area'] > 0)]
    
    logger.info(f"Data cleaning complete. {len(clean_df)} valid records remaining")
    return clean_df

def save_to_database(df):
    """Save cleaned data to database."""
    try:
        with Session(engine) as session:
            count = 0
            for _, row in df.iterrows():
                prop_dict = row.to_dict()
                # Validate before inserting
                clean_prop = validate_property(prop_dict)
                if clean_prop:
                    property_obj = Property(**clean_prop)
                    session.add(property_obj)
                    count += 1
            
            session.commit()
            logger.info(f"Successfully saved {count} properties to database")
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise

def main(file_path=None):
    """Main function to run the data cleansing process."""
    try:
        if file_path:
            # If file path provided, read from file
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif file_path.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file_path)
            else:
                logger.error(f"Unsupported file format: {file_path}")
                return
        else:
            # Example data for testing
            logger.info("No file provided, using test data")
            test_data = {
                'address': ['123 Main St', '456 Oak Ave', '789 Pine Rd', '101 Elm St'],
                'price': ['$250,000', '$450,000', 'unknown', '$325,500'],
                'area': ['1,200 sq ft', '2,100 sq ft', '950 sq ft', '1,800 sq ft'],
                'date_listed': ['2023-01-15', '01/25/2023', '2023-02-10', '03/15/2023']
            }
            df = pd.DataFrame(test_data)
        
        # Clean the data
        clean_df = clean_dataframe(df)
        
        # Save to database
        save_to_database(clean_df)
        
        # Optionally save cleaned data to new file
        output_file = 'cleaned_properties.csv'
        clean_df.to_csv(output_file, index=False)
        logger.info(f"Cleaned data saved to {output_file}")
        
        return clean_df
    
    except Exception as e:
        logger.error(f"Error in data cleansing process: {str(e)}")
        raise

if __name__ == "__main__":
    import sys
    file_path = sys.argv[1] if len(sys.argv) > 1 else None
    main(file_path)