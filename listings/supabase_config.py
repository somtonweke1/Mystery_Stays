from supabase import create_client, Client
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Supabase configuration
SUPABASE_URL = "https://jdtutawicevgeylekgja.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpkdHV0YXdpY2V2Z2V5bGVrZ2phIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDYxMTExMjYsImV4cCI6MjA2MTY4NzEyNn0.8peVKHZMIgpm5WKP_M5zBsaLj4vn0rXL5zAVQIYhJmM"
SUPABASE_SERVICE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpkdHV0YXdpY2V2Z2V5bGVrZ2phIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc0NjExMTEyNiwiZXhwIjoyMDYxNjg3MTI2fQ.zM2SKjokolSt0fwNVPA4gm_XNBIXUtgaCkneJL0lLe8"

# Initialize Supabase client
supabase: Client = create_client(
    supabase_url=SUPABASE_URL,
    supabase_key=SUPABASE_KEY
)

# Initialize Supabase service client for admin operations
supabase_service: Client = create_client(
    supabase_url=SUPABASE_URL,
    supabase_key=SUPABASE_SERVICE_KEY
)

# Property table name
PROPERTIES_TABLE = "properties"
IMAGES_TABLE = "property_images"
AMENITIES_TABLE = "amenities"
PROPERTY_AMENITIES_TABLE = "property_amenities"
LOCATIONS_TABLE = "locations"
LANDLORDS_TABLE = "landlords"
BOOKINGS_TABLE = "bookings" 