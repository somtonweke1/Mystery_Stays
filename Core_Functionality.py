from flask import Flask, request, jsonify
from sqlalchemy import create_engine, Column, Integer, String, Boolean, Float, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import hashlib
from datetime import datetime
import logging

# Initialize Flask app
app = Flask(__name__)

# Database setup
Base = declarative_base()
engine = create_engine('sqlite:///realestate.db')  # For production, use a more robust DB
Session = sessionmaker(bind=engine)

# Models
class UserProfile(Base):
    __tablename__ = 'users'
    
    id = Column(String, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    preferences = Column(JSON)  # Store preferences as JSON
    search_history = Column(JSON)  # Store search history as JSON
    saved_properties = Column(JSON)  # Store saved property IDs as JSON array
    usage_count = Column(Integer, default=0)  # Track API usage
    last_reset = Column(DateTime)  # Track when usage count was last reset
    premium = Column(Boolean, default=False)  # Premium user flag

class Property(Base):
    __tablename__ = 'properties'
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    address = Column(String, nullable=False)
    neighborhood = Column(String)
    coordinates = Column(JSON)  # Store [lat, lng] as JSON
    bedrooms = Column(Integer)
    bathrooms = Column(Float)
    rent = Column(Integer)
    deposit = Column(Integer)
    accepted_vouchers = Column(JSON)  # Store voucher types as JSON array
    features = Column(JSON)  # Store features as JSON array
    description = Column(String)
    landlord = Column(String)
    image_url = Column(String)
    listing_source = Column(String)
    available_date = Column(DateTime)
    active = Column(Boolean, default=True)

# Create tables if they don't exist
Base.metadata.create_all(engine)

# User authentication and profile routes
@app.route('/auth/register', methods=['POST'])
def register_user():
    data = request.json
    
    # Validate required fields
    required_fields = ["email", "password", "name"]
    for field in required_fields:
        if field not in data:
            return jsonify({"status": "error", "message": f"Missing required field: {field}"}), 400
    
    # Check if user already exists
    session = Session()
    existing_user = session.query(UserProfile).filter_by(email=data['email']).first()
    if existing_user:
        session.close()
        return jsonify({"status": "error", "message": "User already exists"}), 400
    
    # Create user profile
    user_id = hashlib.md5(data['email'].encode()).hexdigest()
    new_user = UserProfile(
        id=user_id,
        email=data['email'],
        name=data['name'],
        preferences={},
        search_history=[],
        saved_properties=[],
        usage_count=0,
        last_reset=datetime.utcnow(),
        premium=False
    )
    
    # In a real app, we'd hash the password and implement proper auth
    # For this demo, we're just storing the profile info
    
    try:
        session.add(new_user)
        session.commit()
        return jsonify({
            "status": "success", 
            "message": "User registered successfully",
            "user_id": user_id
        })
    except Exception as e:
        session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()

@app.route('/user/preferences', methods=['POST'])
def update_preferences():
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({"status": "error", "message": "User ID required"}), 400
    
    preferences = data.get('preferences', {})
    
    # Update user preferences in database
    session = Session()
    try:
        user = session.query(UserProfile).filter_by(id=user_id).first()
        if not user:
            session.close()
            return jsonify({"status": "error", "message": "User not found"}), 404
            
        # Merge new preferences with existing ones
        current_prefs = user.preferences if user.preferences else {}
        updated_prefs = {**current_prefs, **preferences}
        user.preferences = updated_prefs
        
        session.commit()
        return jsonify({
            "status": "success", 
            "message": "Preferences updated successfully",
            "preferences": updated_prefs
        })
    except Exception as e:
        session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()

@app.route('/user/saved_properties', methods=['POST'])
def save_property():
    data = request.json
    user_id = data.get('user_id')
    property_id = data.get('property_id')
    
    if not user_id or not property_id:
        return jsonify({"status": "error", "message": "User ID and Property ID required"}), 400
    
    # Update saved properties
    session = Session()
    try:
        user = session.query(UserProfile).filter_by(id=user_id).first()
        if not user:
            session.close()
            return jsonify({"status": "error", "message": "User not found"}), 404
            
        # Add property to saved list if not already saved
        saved = user.saved_properties if user.saved_properties else []
        if property_id not in saved:
            saved.append(property_id)
            user.saved_properties = saved
            
        session.commit()
        return jsonify({
            "status": "success", 
            "message": "Property saved successfully",
            "saved_properties": saved
        })
    except Exception as e:
        session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()

@app.route('/user/saved_properties', methods=['GET'])
def get_saved_properties():
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({"status": "error", "message": "User ID required"}), 400
    
    # Get saved properties with details
    session = Session()
    try:
        user = session.query(UserProfile).filter_by(id=user_id).first()
        if not user:
            session.close()
            return jsonify({"status": "error", "message": "User not found"}), 404
            
        saved_ids = user.saved_properties if user.saved_properties else []
        
        # Fetch property details
        saved_properties = []
        if saved_ids:
            properties = session.query(Property).filter(Property.id.in_(saved_ids)).all()
            saved_properties = [
                {
                    "id": p.id,
                    "title": p.title,
                    "address": p.address,
                    "neighborhood": p.neighborhood,
                    "bedrooms": p.bedrooms,
                    "rent": p.rent,
                    "accepted_vouchers": p.accepted_vouchers,
                    "landlord": p.landlord,
                    "image_url": p.image_url,
                    "listing_source": p.listing_source
                }
                for p in properties
            ]
            
        return jsonify({
            "status": "success", 
            "saved_properties": saved_properties
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()

# Enhanced property search with AI recommendations
@app.route('/properties/recommended', methods=['GET'])
def get_recommended_properties():
    user_id = request.args.get('user_id')
    limit = int(request.args.get('limit', 10))
    
    if not user_id:
        return jsonify({"status": "error", "message": "User ID required"}), 400
    
    # Track usage and check limits
    session = Session()
    try:
        user = session.query(UserProfile).filter_by(id=user_id).first()
        if not user:
            session.close()
            return jsonify({"status": "error", "message": "User not found"}), 404
        
        # Check if daily limit reached for free users
        if not user.premium:
            # Reset usage count if it's a new day
            today = datetime.utcnow().date()
            last_reset = user.last_reset.date() if user.last_reset else None
            
            if last_reset != today:
                user.usage_count = 0
                user.last_reset = datetime.utcnow()
            
            if user.usage_count >= 10:  # Daily limit for free tier
                session.close()
                return jsonify({
                    "status": "limit_reached", 
                    "message": "Daily search limit reached. Upgrade to premium or try again tomorrow.",
                    "remaining": 0
                }), 429
            
            # Increment usage count
            user.usage_count += 1
        
        session.commit()
        
        # Get user preferences
        preferences = user.preferences if user.preferences else {}
        
        # Get recommended properties based on preferences
        recommended = recommend_properties_for_user(user_id, preferences, limit)
        
        return jsonify({
            "status": "success", 
            "properties": recommended,
            "remaining_searches": None if user.premium else (10 - user.usage_count)
        })
    except Exception as e:
        session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()

# AI recommendation engine
def recommend_properties_for_user(user_id, preferences, limit=10):
    """Generate personalized property recommendations"""
    session = Session()
    try:
        # Basic filtering based on preferences
        query = session.query(Property).filter(Property.active == True)
        
        # Apply filters from preferences
        if preferences.get('neighborhoods'):
            query = query.filter(Property.neighborhood.in_(preferences['neighborhoods']))
        
        if preferences.get('max_rent'):
            query = query.filter(Property.rent <= preferences['max_rent'])
            
        if preferences.get('bedrooms') and preferences['bedrooms'] != 'Any':
            query = query.filter(Property.bedrooms == preferences['bedrooms'])
            
        if preferences.get('voucher_types'):
            # This is simplified - in reality you'd need a more complex query to check array contents
            # For a proper implementation, use a database that supports array operations like PostgreSQL
            query = query.filter(Property.accepted_vouchers.overlap(preferences['voucher_types']))
        
        # Get recent search history to boost similar properties
        user = session.query(UserProfile).filter_by(id=user_id).first()
        search_history = user.search_history if user and user.search_history else []
        
        # Get properties that match basic criteria
        matching_properties = query.all()
        
        # In a real AI recommendation system, we would score each property based on multiple factors
        # Here's a simplified scoring approach:
        scored_properties = []
        for prop in matching_properties:
            score = 0
            
            # Boost score for properties in recently searched neighborhoods
            for search in search_history[-5:]:  # Look at last 5 searches
                if search.get('neighborhood') == prop.neighborhood:
                    score += 10
                    
                # Boost for price match (within 10% of searched price)
                if search.get('price') and abs(search['price'] - prop.rent) / search['price'] < 0.1:
                    score += 5
                    
                # Boost for bedrooms match
                if search.get('bedrooms') and search['bedrooms'] == prop.bedrooms:
                    score += 5
            
            # Additional scoring based on preferences
            if preferences.get('preferred_features'):
                for feature in preferences['preferred_features']:
                    if feature in prop.features:
                        score += 3
            
            # Boost properties with the same landlord as previously viewed/saved
            if preferences.get('preferred_landlords') and prop.landlord in preferences['preferred_landlords']:
                score += 8
                
            # Penalize properties that are far from preferred locations (if applicable)
            if preferences.get('preferred_locations') and prop.coordinates:
                # This would require a distance calculation based on coordinates
                # Simplified version:
                for location in preferences['preferred_locations']:
                    distance = calculate_distance(location, prop.coordinates)
                    if distance < 2:  # Within 2 miles/km
                        score += 5
                    elif distance < 5:  # Within 5 miles/km
                        score += 2
            
            scored_properties.append((prop, score))
        
        # Sort by score (descending)
        scored_properties.sort(key=lambda x: x[1], reverse=True)
        
        # Return top N properties
        top_properties = [
            {
                "id": p[0].id,
                "title": p[0].title,
                "address": p[0].address,
                "neighborhood": p[0].neighborhood,
                "bedrooms": p[0].bedrooms,
                "rent": p[0].rent,
                "accepted_vouchers": p[0].accepted_vouchers,
                "landlord": p[0].landlord,
                "image_url": p[0].image_url,
                "listing_source": p[0].listing_source,
                "relevance_score": p[1],
                "features": p[0].features
            }
            for p in scored_properties[:limit]
        ]
        
        # Update user's search history with this search
        if user:
            # Add current search parameters to history
            if len(search_history) >= 20:  # Keep history to reasonable size
                search_history = search_history[1:]  # Remove oldest search
            
            # Add current search parameters
            current_search = {
                'timestamp': datetime.utcnow().isoformat(),
                'preferences': preferences
            }
            search_history.append(current_search)
            user.search_history = search_history
            session.commit()
        
        return top_properties
        
    except Exception as e:
        session.rollback()
        logging.error(f"Error in recommendation engine: {str(e)}")
        return []  # Return empty list on error
    finally:
        session.close()

# Helper function for distance calculation
def calculate_distance(point1, point2):
    """
    Calculate distance between two points (latitude, longitude)
    Returns distance in miles/km
    """
    # Simplified distance calculation - in a real app, use a proper geospatial library
    # This is a crude approximation using Euclidean distance
    # For accurate distance, use the Haversine formula or a geospatial library
    return ((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)**0.5

# Basic property routes
@app.route('/properties', methods=['GET'])
def search_properties():
    # Get search parameters
    neighborhood = request.args.get('neighborhood')
    min_bedrooms = request.args.get('min_bedrooms')
    max_rent = request.args.get('max_rent')
    voucher_type = request.args.get('voucher_type')
    limit = int(request.args.get('limit', 20))
    offset = int(request.args.get('offset', 0))
    
    # Build query
    session = Session()
    try:
        query = session.query(Property).filter(Property.active == True)
        
        if neighborhood:
            query = query.filter(Property.neighborhood == neighborhood)
            
        if min_bedrooms:
            query = query.filter(Property.bedrooms >= int(min_bedrooms))
            
        if max_rent:
            query = query.filter(Property.rent <= int(max_rent))
            
        if voucher_type:
            # This is simplified - in a real app, you'd need a more complex query
            # to check if the voucher type is in the accepted_vouchers array
            pass
            
        # Get total count for pagination
        total_count = query.count()
        
        # Apply pagination
        properties = query.offset(offset).limit(limit).all()
        
        # Format results
        results = [
            {
                "id": p.id,
                "title": p.title,
                "address": p.address,
                "neighborhood": p.neighborhood, 
                "bedrooms": p.bedrooms,
                "rent": p.rent,
                "accepted_vouchers": p.accepted_vouchers,
                "landlord": p.landlord,
                "image_url": p.image_url,
                "listing_source": p.listing_source
            }
            for p in properties
        ]
        
        return jsonify({
            "status": "success",
            "properties": results,
            "total": total_count,
            "page": offset // limit + 1,
            "total_pages": (total_count + limit - 1) // limit
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()

@app.route('/properties/<property_id>', methods=['GET'])
def get_property_details(property_id):
    session = Session()
    try:
        property = session.query(Property).filter_by(id=property_id).first()
        
        if not property:
            session.close()
            return jsonify({"status": "error", "message": "Property not found"}), 404
            
        # Format full property details
        details = {
            "id": property.id,
            "title": property.title,
            "address": property.address,
            "neighborhood": property.neighborhood,
            "bedrooms": property.bedrooms,
            "bathrooms": property.bathrooms,
            "rent": property.rent,
            "deposit": property.deposit,
            "accepted_vouchers": property.accepted_vouchers,
            "features": property.features,
            "description": property.description,
            "landlord": property.landlord,
            "image_url": property.image_url,
            "listing_source": property.listing_source,
            "available_date": property.available_date.isoformat() if property.available_date else None
        }
        
        return jsonify({
            "status": "success",
            "property": details
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally: 
        session.close()

# Admin routes for property management
@app.route('/admin/properties', methods=['POST'])
def add_property():
    # In a real app, this would require admin authentication
    data = request.json
    
    # Validate required fields
    required_fields = ["title", "address", "rent"]
    for field in required_fields:
        if field not in data:
            return jsonify({"status": "error", "message": f"Missing required field: {field}"}), 400
    
    # Create property ID
    property_id = hashlib.md5((data['address'] + str(datetime.utcnow())).encode()).hexdigest()
    
    # Create new property
    new_property = Property(
        id=property_id,
        title=data.get('title'),
        address=data.get('address'),
        neighborhood=data.get('neighborhood'),
        coordinates=data.get('coordinates'),
        bedrooms=data.get('bedrooms'),
        bathrooms=data.get('bathrooms'),
        rent=data.get('rent'),
        deposit=data.get('deposit'),
        accepted_vouchers=data.get('accepted_vouchers', []),
        features=data.get('features', []),
        description=data.get('description'),
        landlord=data.get('landlord'),
        image_url=data.get('image_url'),
        listing_source=data.get('listing_source'),
        available_date=datetime.fromisoformat(data['available_date']) if data.get('available_date') else None,
        active=True
    )
    
    session = Session()
    try:
        session.add(new_property)
        session.commit()
        return jsonify({
            "status": "success",
            "message": "Property added successfully",
            "property_id": property_id
        })
    except Exception as e:
        session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()

@app.route('/admin/properties/<property_id>', methods=['PUT'])
def update_property(property_id):
    # In a real app, this would require admin authentication
    data = request.json
    
    session = Session()
    try:
        property = session.query(Property).filter_by(id=property_id).first()
        
        if not property:
            session.close()
            return jsonify({"status": "error", "message": "Property not found"}), 404
            
        # Update property fields
        for key, value in data.items():
            if hasattr(property, key):
                if key == 'available_date' and value:
                    value = datetime.fromisoformat(value)
                setattr(property, key, value)
                
        session.commit()
        return jsonify({
            "status": "success",
            "message": "Property updated successfully"
        })
    except Exception as e:
        session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()

@app.route('/admin/properties/<property_id>/deactivate', methods=['POST'])
def deactivate_property(property_id):
    # In a real app, this would require admin authentication
    session = Session()
    try:
        property = session.query(Property).filter_by(id=property_id).first()
        
        if not property:
            session.close()
            return jsonify({"status": "error", "message": "Property not found"}), 404
            
        property.active = False
        session.commit()
        return jsonify({
            "status": "success",
            "message": "Property deactivated successfully"
        })
    except Exception as e:
        session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()

# Utility routes
@app.route('/neighborhoods', methods=['GET'])
def get_neighborhoods():
    session = Session()
    try:
        # Get unique neighborhoods
        neighborhoods = session.query(Property.neighborhood).distinct().all()
        neighborhood_list = [n[0] for n in neighborhoods if n[0]]
        
        return jsonify({
            "status": "success",
            "neighborhoods": neighborhood_list
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        session.close()

# Run the app
if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run Flask app
    app.run(debug=True)