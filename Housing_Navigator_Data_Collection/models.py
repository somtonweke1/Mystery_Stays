from sqlalchemy import Column, String, Float, Integer, DateTime, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# Create base class for SQLAlchemy models
Base = declarative_base()

class Property(Base):
    """Model for housing properties"""
    __tablename__ = 'properties'
    
    # Primary key
    id = Column(String, primary_key=True)
    
    # Basic property information
    title = Column(String)
    address = Column(String)
    neighborhood = Column(String)
    bedrooms = Column(String)
    bathrooms = Column(String)
    rent = Column(Float)
    accepted_vouchers = Column(JSON)  # Store as JSON array
    landlord = Column(String)
    date_available = Column(String)
    
    # Additional details
    amenities = Column(JSON)  # Store as JSON array
    description = Column(String)
    image_url = Column(String)
    subway_lines = Column(JSON)  # Store as JSON array
    
    # Source tracking
    listing_source = Column(String)
    listing_url = Column(String)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Property(id='{self.id}', title='{self.title}', rent={self.rent})>"

# Create database engine
# Using SQLite for simplicity - change connection string as needed
engine = create_engine('sqlite:///housing_navigator.db')

# Create all tables
Base.metadata.create_all(engine)