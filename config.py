"""
Configuration File
Centralized configuration for the lead generation system

Set API keys via environment variables or update this file directly.
"""

import os
from typing import Dict, Any, Optional

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # If python-dotenv is not installed, environment variables need to be set manually
    pass

# API Configuration
# Set these via environment variables for security
CONFIG: Dict[str, Any] = {
    # ORCID API
    "orcid_client_id": os.getenv("ORCID_CLIENT_ID", None),  # Optional for public API
    "orcid_client_secret": os.getenv("ORCID_CLIENT_SECRET", None),  # Optional for public API
    "orcid_use_sandbox": os.getenv("ORCID_USE_SANDBOX", "false").lower() == "true",  # Use sandbox for testing
    
    # PubMed API
    "pubmed_email": os.getenv("PUBMED_EMAIL", "dummyuser@gmail.com"),
    "pubmed_api_key": os.getenv("PUBMED_API_KEY", "a41f6c46cbe9f3aa7ad3cb1f11d7ead15409"),  # Optional, increases rate limit
    
    # Email Finder API
    "email_provider": os.getenv("EMAIL_PROVIDER", "hunter"),  # hunter, apollo, clearbit, pattern
    "email_api_key": os.getenv("EMAIL_API_KEY", "43ea8733aa387143601401bc11235d591d7ba6eb"),
    
    # Serp API (Google Search)
    "serp_api_key": os.getenv("SERP_API_KEY", "23902410-066a-4407-9612-150d13e6915e"),
    "serp_engine": os.getenv("SERP_ENGINE", "google"),  # google, scholar, news, etc.
    
    # Google Maps API (for geocoding)
    "google_maps_api_key": os.getenv("GOOGLE_MAPS_API_KEY", "AIzaSyAYC6m5JZyYZuYR_VH1sY7a4aV3qJxQ-b4"),
    
    # Funding API
    "funding_source": os.getenv("FUNDING_SOURCE", "nih_reporter"),  # nih_reporter, cordis
    "funding_api_key": os.getenv("FUNDING_API_KEY", "b6794065-4460-4305-9473-90100176561e"),  # Not required for NIH RePORTER or CORDIS
    
    # Database
    "database_path": os.getenv("DATABASE_PATH", "leads.db"),
    
    # Output
    "output_dir": os.getenv("OUTPUT_DIR", "output"),
    
    # Scoring weights (can be customized)
    "scoring_weights": {
        "role_fit": {
            "title_keywords": ["toxicology", "safety", "hepatic", "3d", "preclinical", "drug safety"],
            "weight": 30
        },
        "scientific_intent": {
            "weight": 40,
            "keywords": ["DILI", "liver injury", "in vitro", "3D cell culture", "organoid", "spheroid"]
        },
        "company_intent": {
            "weight": 20,
            "timeframe_days": 365
        },
        "technographic": {
            "company_uses_similar_tech": 15,
            "company_open_to_nams": 10
        },
        "location": {
            "hubs": ["boston", "cambridge", "bay area", "san francisco", "basel", "san diego"],
            "weight": 15,
            "remote_bonus": 10
        }
    },
    
    # Biotech hubs
    "biotech_hubs": [
        "Cambridge, MA",
        "Boston, MA",
        "San Francisco, CA",
        "San Diego, CA",
        "Research Triangle Park, NC",
        "Seattle, WA",
        "New York, NY",
        "Basel, Switzerland",
        "London, UK"
    ],
    
    # Rate limiting
    "rate_limits": {
        "orcid": 1.0,  # seconds between requests
        "pubmed": 0.34,   # NCBI requires max 3 requests/second
        "email": 1.0,
        "funding": 1.0,
        "serp": 1.0  # seconds between Serp API requests
    }
}


def get_config() -> Dict[str, Any]:
    """
    Get configuration dictionary.
    
    Returns:
        Configuration dictionary
    """
    return CONFIG


def get_api_key(service: str) -> Optional[str]:
    """
    Get API key for a service.
    
    Args:
        service: Service name (e.g., "orcid", "email", "pubmed")
    
    Returns:
        API key or None
    """
    key_map = {
        "orcid": "orcid_client_id",  # Note: ORCID uses client_id/client_secret, not single API key
        "email": "email_api_key",
        "pubmed": "pubmed_api_key",
        "google_maps": "google_maps_api_key",
        "funding": "funding_api_key",
        "serp": "serp_api_key"
    }
    
    key_name = key_map.get(service.lower())
    if key_name:
        return CONFIG.get(key_name)
    
    return None


def update_config(updates: Dict[str, Any]):
    """
    Update configuration with new values.
    
    Args:
        updates: Dictionary of configuration updates
    """
    CONFIG.update(updates)


if __name__ == "__main__":
    # Print current configuration (without sensitive keys)
    print("Current Configuration:")
    for key, value in CONFIG.items():
        if "key" in key.lower() or "api" in key.lower():
            print(f"  {key}: {'***' if value else 'Not set'}")
        else:
            print(f"  {key}: {value}")

