# Mystery Stays

A Django-based platform for finding and managing voucher-friendly housing listings. This project provides an API for accessing property listings that accept housing vouchers (like Section 8) and includes web scrapers to aggregate listings from popular housing websites.

## Features

- REST API for querying property listings
- Admin interface for managing properties, landlords, and voucher information
- Scrapers for popular housing sites (Zillow, Apartments.com)
- Filtering properties by location, price, bedrooms, and more
- Voucher type tracking and filtering

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository:
```bash
git clone https://github.com/somtonweke1/Mystery_Stays.git
cd Mystery_Stays
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

4. Run the database migrations:
```bash
python manage.py migrate
```

5. Create a superuser for the admin interface:
```bash
python manage.py createsuperuser
```

6. Run the development server:
```bash
python manage.py runserver
```

### Running the Scrapers

To populate the database with property listings, run the following command:
```bash
python manage.py run_scrapers --locations "New York" "Los Angeles" "Chicago"
```

You can specify as many locations as you want, and the scrapers will search for voucher-friendly properties in each location.

## API Endpoints

- `/api/properties/` - List and filter properties
- `/api/landlords/` - List landlords
- `/api/locations/` - List locations
- `/api/voucher-types/` - List voucher types
- `/api/amenities/` - List amenities

### Filtering Examples:

- `/api/properties/?bedrooms=2` - Properties with 2 bedrooms
- `/api/properties/?location__city=New%20York` - Properties in New York
- `/api/properties/?rent_amount_lte=1500` - Properties with rent <= $1,500
- `/api/properties/?voucher_types=1` - Properties accepting a specific voucher type

## Project Structure

- `listings/` - Main Django app for managing property listings
  - `models.py` - Data models for properties, landlords, etc.
  - `views.py` - API views using Django REST Framework
  - `serializers.py` - JSON serializers for the API
  - `admin.py` - Admin interface configuration
  - `scrapers/` - Web scrapers for property listings
    - `base.py` - Base scraper class
    - `zillow.py` - Zillow-specific scraper
    - `apartments.py` - Apartments.com-specific scraper
    - `utils.py` - Utility functions for running scrapers
  - `management/commands/` - Custom Django management commands
    - `run_scrapers.py` - Command to run the scrapers

## License

This project is licensed under the MIT License - see the LICENSE file for details.