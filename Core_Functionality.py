# Core_Functionality.py

import datetime
from typing import List, Dict, Any

class MysteryStayAgent:
    def __init__(self):
        self.available_properties = []
        self.user_preferences = {}
        self.booked_stays = {}

    def add_available_property(self, property_details: Dict[str, Any]) -> str:
        """Add a vacant property to the pool at a 50% discount."""
        property_id = f"prop_{len(self.available_properties) + 1}"
        property_details = property_details.copy()
        property_details["id"] = property_id
        property_details["discount_price"] = property_details["original_price"] * 0.5
        self.available_properties.append(property_details)
        return property_id

    def register_user_preferences(self, user_id: str, preferences: Dict[str, Any]) -> None:
        """Register a digital nomad's preferences."""
        self.user_preferences[user_id] = preferences

    def match_user_to_properties(self, user_id: str) -> List[Dict[str, Any]]:
        """Find properties matching user preferences, hiding exact location."""
        if user_id not in self.user_preferences:
            return []
        preferences = self.user_preferences[user_id]
        matched = []
        for prop in self.available_properties:
            matches = True
            for key in preferences:
                if key == "location":
                    continue  # Hide location for mystery stays
                if key == "price_max" and prop["discount_price"] > preferences[key]:
                    matches = False
                elif key == "amenities" and not all(a in prop.get("amenities", []) for a in preferences[key]):
                    matches = False
                elif key not in ["price_max", "amenities"] and preferences[key] != prop.get(key):
                    matches = False
            if matches:
                # Hide exact location, show region
                mystery_prop = prop.copy()
                if "address" in mystery_prop:
                    del mystery_prop["address"]
                if "location" in mystery_prop:
                    mystery_prop["region"] = self._get_region(mystery_prop["location"])
                    del mystery_prop["location"]
                matched.append(mystery_prop)
        return matched

    def book_mystery_stay(self, user_id: str, property_id: str, check_in: datetime.date, check_out: datetime.date) -> Dict[str, Any]:
        """Book a mystery stay and return confirmation (location hidden)."""
        property_details = next((p for p in self.available_properties if p["id"] == property_id), None)
        if not property_details:
            return {"status": "failed", "reason": "Property not found"}
        booking_id = f"book_{len(self.booked_stays) + 1}"
        nights = (check_out - check_in).days
        booking = {
            "booking_id": booking_id,
            "user_id": user_id,
            "property_id": property_id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "total_price": property_details["discount_price"] * nights,
            "status": "confirmed",
            "property_details": property_details
        }
        self.booked_stays[booking_id] = booking
        confirmation = booking.copy()
        confirmation["property_details"] = self._get_limited_property_details(property_details)
        return confirmation

    def reveal_location(self, booking_id: str) -> Dict[str, Any]:
        """Reveal the exact location of a booked mystery stay."""
        booking = self.booked_stays.get(booking_id)
        if not booking:
            return {"status": "failed", "reason": "Booking not found"}
        return booking["property_details"]

    def _get_region(self, location: Dict[str, Any]) -> str:
        """Extract region info from location."""
        return f"{location.get('city', 'Unknown City')}, {location.get('country', 'Unknown Country')}"

    def _get_limited_property_details(self, property_details: Dict[str, Any]) -> Dict[str, Any]:
        """Hide location details, show only region."""
        limited = property_details.copy()
        for key in ["address", "location", "coordinates", "directions"]:
            if key in limited:
                del limited[key]
        if "location" in property_details:
            limited["region"] = self._get_region(property_details["location"])
        return limited