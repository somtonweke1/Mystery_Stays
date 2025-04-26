from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import Landlord, Location, VoucherType, Property, Amenity


class PropertyModelTest(TestCase):
    """Test cases for the Property model"""
    
    def setUp(self):
        # Create test data
        self.landlord = Landlord.objects.create(
            name="Test Landlord",
            email="test@example.com",
            phone="555-1234",
            voucher_friendly=True
        )
        
        self.location = Location.objects.create(
            city="Test City",
            state="TS",
            country="United States",
            zip_code="12345"
        )
        
        self.voucher_type = VoucherType.objects.create(
            name="Section 8",
            description="Housing Choice Voucher Program"
        )
        
        self.property = Property.objects.create(
            title="Test Property",
            description="A test property description",
            property_type="apartment",
            bedrooms=2,
            bathrooms=1.5,
            square_feet=1000,
            rent_amount=1500.00,
            deposit_amount=1500.00,
            landlord=self.landlord,
            location=self.location,
            is_available=True,
            source="manual"
        )
        
        self.property.voucher_types.add(self.voucher_type)
    
    def test_property_creation(self):
        """Test that a property can be created with the expected attributes"""
        self.assertEqual(self.property.title, "Test Property")
        self.assertEqual(self.property.bedrooms, 2)
        self.assertEqual(self.property.bathrooms, 1.5)
        self.assertEqual(self.property.rent_amount, 1500.00)
        self.assertEqual(self.property.landlord, self.landlord)
        self.assertEqual(self.property.location, self.location)
        self.assertTrue(self.property.is_available)
        
        # Test many-to-many relationship
        self.assertEqual(self.property.voucher_types.count(), 1)
        self.assertEqual(self.property.voucher_types.first(), self.voucher_type)
    
    def test_property_string_representation(self):
        """Test the string representation of a property"""
        expected = f"Test Property - Test City, TS"
        self.assertEqual(str(self.property), expected)


class PropertyAPITest(TestCase):
    """Test cases for the Property API endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create test data
        self.landlord = Landlord.objects.create(
            name="API Test Landlord",
            voucher_friendly=True
        )
        
        self.location = Location.objects.create(
            city="API City",
            state="AC",
            country="United States"
        )
        
        self.property = Property.objects.create(
            title="API Test Property",
            property_type="apartment",
            bedrooms=1,
            bathrooms=1.0,
            rent_amount=1200.00,
            landlord=self.landlord,
            location=self.location,
            is_available=True
        )
        
        self.amenity = Amenity.objects.create(name="Test Amenity")
    
    def test_property_list_endpoint(self):
        """Test retrieving a list of properties"""
        url = reverse('property-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
    
    def test_property_detail_endpoint(self):
        """Test retrieving a single property"""
        url = reverse('property-detail', args=[self.property.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "API Test Property")
        self.assertEqual(response.data['rent_amount'], '1200.00')  # Note: Decimal as string in JSON
        self.assertEqual(response.data['landlord']['name'], "API Test Landlord")
        self.assertEqual(response.data['location']['city'], "API City")
    
    def test_filtering_properties(self):
        """Test filtering properties by various criteria"""
        # Create another property for testing filters
        Property.objects.create(
            title="Expensive Property",
            property_type="house",
            bedrooms=3,
            bathrooms=2.0,
            rent_amount=2500.00,
            landlord=self.landlord,
            location=self.location,
            is_available=True
        )
        
        # Test filtering by bedrooms
        url = reverse('property-list')
        response = self.client.get(url, {'bedrooms': 1})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], "API Test Property")
        
        # Test filtering by property_type
        response = self.client.get(url, {'property_type': 'house'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['title'], "Expensive Property")