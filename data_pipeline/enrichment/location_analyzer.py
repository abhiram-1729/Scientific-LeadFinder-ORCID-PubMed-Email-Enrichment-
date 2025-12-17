"""
Location Analyzer Module
Distinguishes personal location vs company HQ and geocodes locations

This module analyzes and enriches location data.
"""

import requests
from typing import Dict, Any, Optional
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LocationAnalyzer:
    """
    Analyzes and enriches location data.
    """
    
    def __init__(self, google_maps_api_key: Optional[str] = None):
        """
        Initialize location analyzer.
        
        Args:
            google_maps_api_key: Optional Google Maps API key for geocoding
        """
        self.google_maps_api_key = google_maps_api_key
        self.biotech_hubs = [
            "Cambridge, MA",
            "Boston, MA",
            "San Francisco, CA",
            "San Diego, CA",
            "Research Triangle Park, NC",
            "Seattle, WA",
            "New York, NY",
            "Basel, Switzerland",
            "London, UK"
        ]
    
    def analyze_location(
        self,
        personal_location: Optional[str],
        company_location: Optional[str],
        company_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze location data to determine personal vs company location.
        
        Args:
            personal_location: Personal location string
            company_location: Company headquarters location
            company_name: Optional company name for lookup
        
        Returns:
            Location analysis dictionary
        """
        try:
            # Normalize locations
            personal_loc = self._normalize_location(personal_location) if personal_location else None
            company_loc = self._normalize_location(company_location) if company_location else None
            
            # Determine if remote
            is_remote = False
            if personal_loc and company_loc:
                is_remote = personal_loc.lower() != company_loc.lower()
            
            # Geocode locations
            personal_coords = self._geocode(personal_loc) if personal_loc else None
            company_coords = self._geocode(company_loc) if company_loc else None
            
            # Check if in biotech hub
            is_biotech_hub = False
            hub_name = None
            if personal_loc:
                for hub in self.biotech_hubs:
                    if hub.lower() in personal_loc.lower() or personal_loc.lower() in hub.lower():
                        is_biotech_hub = True
                        hub_name = hub
                        break
            
            # Extract state/country
            personal_state = self._extract_state(personal_loc) if personal_loc else None
            company_state = self._extract_state(company_loc) if company_loc else None
            
            return {
                "personal_location": personal_loc,
                "company_hq": company_loc,
                "is_remote": is_remote,
                "remote_status": f"Remote in {personal_state}" if (is_remote and personal_state) else None,
                "is_biotech_hub": is_biotech_hub,
                "biotech_hub_name": hub_name,
                "personal_coordinates": personal_coords,
                "company_coordinates": company_coords,
                "personal_state": personal_state,
                "company_state": company_state,
                "location_match": not is_remote if (personal_loc and company_loc) else None
            }
        
        except Exception as e:
            logger.error(f"Error analyzing location: {str(e)}")
            return {
                "personal_location": personal_location,
                "company_hq": company_location,
                "error": str(e)
            }
    
    def _normalize_location(self, location: str) -> str:
        """Normalize location string."""
        if not location:
            return ""
        
        # Remove extra whitespace
        location = " ".join(location.split())
        
        # Standardize common abbreviations
        replacements = {
            "Massachusetts": "MA",
            "California": "CA",
            "North Carolina": "NC",
            "Washington": "WA",
            "New York": "NY"
        }
        
        for full, abbrev in replacements.items():
            location = location.replace(full, abbrev)
        
        return location.strip()
    
    def _geocode(self, location: str) -> Optional[Dict[str, float]]:
        """
        Geocode location using Google Maps API or fallback.
        
        Args:
            location: Location string
        
        Returns:
            Dictionary with lat/lng or None
        """
        if not location:
            return None
        
        try:
            if self.google_maps_api_key:
                return self._geocode_google_maps(location)
            else:
                return None
        
        except Exception as e:
            logger.error(f"Error geocoding {location}: {str(e)}")
            return None
    
    def _geocode_google_maps(self, location: str) -> Optional[Dict[str, float]]:
        """Geocode using Google Maps API."""
        try:
            url = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "address": location,
                "key": self.google_maps_api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get("results"):
                location_data = data["results"][0]["geometry"]["location"]
                return {
                    "lat": location_data["lat"],
                    "lng": location_data["lng"]
                }
        
        except Exception as e:
            logger.error(f"Google Maps geocoding error: {str(e)}")
        
        return None
    
    def _geocode_mock(self, location: str) -> Optional[Dict[str, float]]:
        """Return mock coordinates for known locations."""
        mock_coords = {
            "cambridge, ma": {"lat": 42.3736, "lng": -71.1097},
            "boston, ma": {"lat": 42.3601, "lng": -71.0589},
            "san francisco, ca": {"lat": 37.7749, "lng": -122.4194},
            "san diego, ca": {"lat": 32.7157, "lng": -117.1611},
            "seattle, wa": {"lat": 47.6062, "lng": -122.3321},
            "new york, ny": {"lat": 40.7128, "lng": -74.0060}
        }
        
        location_lower = location.lower()
        for key, coords in mock_coords.items():
            if key in location_lower or location_lower in key:
                return coords
        
        return None
    
    def _extract_state(self, location: str) -> Optional[str]:
        """Extract state from location string."""
        if not location:
            return None
        
        # Common state patterns
        state_pattern = r'\b([A-Z]{2})\b'
        match = re.search(state_pattern, location)
        if match:
            return match.group(1)
        
        # Check for full state names
        state_names = {
            "massachusetts": "MA",
            "california": "CA",
            "north carolina": "NC",
            "washington": "WA",
            "new york": "NY",
            "texas": "TX",
            "illinois": "IL"
        }
        
        location_lower = location.lower()
        for name, abbrev in state_names.items():
            if name in location_lower:
                return abbrev
        
        return None
    
    def is_biotech_hub(self, location: str) -> bool:
        """
        Check if location is a known biotech hub.
        
        Args:
            location: Location string
        
        Returns:
            True if biotech hub
        """
        location_lower = location.lower()
        for hub in self.biotech_hubs:
            if hub.lower() in location_lower or location_lower in hub.lower():
                return True
        return False


def analyze_profile_location(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to analyze location for a profile.
    
    Args:
        profile: Profile dictionary
    
    Returns:
        Location analysis
    """
    analyzer = LocationAnalyzer()
    return analyzer.analyze_location(
        personal_location=profile.get("location"),
        company_location=profile.get("company_location"),
        company_name=profile.get("company")
    )


if __name__ == "__main__":
    # Test the location analyzer
    analyzer = LocationAnalyzer()
    result = analyzer.analyze_location(
        personal_location="Cambridge, MA",
        company_location="Boston, MA"
    )
    print(f"Personal: {result.get('personal_location')}")
    print(f"Company HQ: {result.get('company_hq')}")
    print(f"Is Remote: {result.get('is_remote')}")
    print(f"Is Biotech Hub: {result.get('is_biotech_hub')}")

