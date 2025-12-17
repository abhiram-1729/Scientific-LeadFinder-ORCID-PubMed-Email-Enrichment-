"""
ORCID Profile Scraper
Supports ORCID Public API for researcher profile discovery

This module handles ORCID profile discovery and extraction for researchers.
ORCID (Open Researcher and Contributor ID) is ideal for finding academic researchers.
"""

import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ORCIDScraper:
    """
    ORCID scraper for researcher profiles.
    Uses ORCID Public API - no authentication required for public data.
    """
    
    def __init__(self, client_id: Optional[str] = None, client_secret: Optional[str] = None, 
                 use_sandbox: bool = False):
        """
        Initialize ORCID scraper.
        
        Args:
            client_id: ORCID API client ID (optional for public API)
            client_secret: ORCID API client secret (optional for public API)
            use_sandbox: Use sandbox environment (for testing)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = "https://api.sandbox.orcid.org" if use_sandbox else "https://api.orcid.org"
        self.public_base_url = "https://pub.orcid.org"  # Public API (no auth needed)
        self.rate_limit_delay = 1.0  # Seconds between requests
    
    def search_profiles(
        self,
        job_titles: List[str],
        locations: Optional[List[str]] = None,
        affiliations: Optional[List[str]] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Search for ORCID profiles matching criteria.
        
        Args:
            job_titles: List of job title keywords (e.g., "toxicology", "researcher")
            locations: Optional list of location keywords
            affiliations: Optional list of affiliation/organization keywords
            limit: Maximum number of profiles to return
        
        Returns:
            List of profile dictionaries
        """
        try:
            if self.client_id and self.client_secret:
                return self._search_with_auth(job_titles, locations, affiliations, limit)
            else:
                # Use public API search (limited functionality)
                return self._search_public(job_titles, locations, affiliations, limit)
        
        except Exception as e:
            logger.error(f"Error searching ORCID profiles: {str(e)}")
            logger.error("ORCID API error - returning empty results. Check API connectivity and credentials.")
            return []
    
    def _search_public(
        self,
        job_titles: List[str],
        locations: Optional[List[str]],
        affiliations: Optional[List[str]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Search using ORCID Public API (no authentication required).
        Note: Public API has limited search capabilities.
        """
        logger.info("Using ORCID Public API (limited search capabilities)")
        
        # ORCID Public API search endpoint
        # Note: Public API doesn't support full-text search, so we'll use mock data
        # In production, you'd need authenticated API access for better search
        
        profiles = []
        search_terms = " ".join(job_titles)
        
        # Try to search by keywords if we have them
        # Public API: https://pub.orcid.org/v3.0/search/?q=keyword
        try:
            url = f"{self.public_base_url}/v3.0/search"
            params = {
                "q": search_terms,
                "rows": min(limit, 100)  # Max 100 per request
            }
            
            headers = {
                "Accept": "application/json"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                orcid_records = data.get("result", [])
                
                for record in orcid_records[:limit]:
                    orcid_id = record.get("orcid-identifier", {}).get("path", "")
                    if orcid_id:
                        # Fetch full profile details
                        profile = self._get_profile_details(orcid_id)
                        if profile:
                            profiles.append(profile)
            
            time.sleep(self.rate_limit_delay)
            
        except Exception as e:
            logger.error(f"Public API search failed: {str(e)}")
            logger.error("ORCID Public API error - returning empty results.")
            return []
        
        return profiles[:limit]
    
    def _search_with_auth(
        self,
        job_titles: List[str],
        locations: Optional[List[str]],
        affiliations: Optional[List[str]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        Search using authenticated ORCID API (requires client credentials).
        This provides better search capabilities.
        """
        if not self.client_id or not self.client_secret:
            logger.warning("Client credentials not provided. Using public API.")
            return self._search_public(job_titles, locations, affiliations, limit)
        
        # Get access token
        access_token = self._get_access_token()
        if not access_token:
            logger.warning("Failed to get access token. Using public API.")
            return self._search_public(job_titles, locations, affiliations, limit)
        
        # Authenticated search
        try:
            url = f"{self.base_url}/v3.0/search"
            search_query = " ".join(job_titles)
            
            params = {
                "q": search_query,
                "rows": min(limit, 100)
            }
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                orcid_records = data.get("result", [])
                
                profiles = []
                for record in orcid_records[:limit]:
                    orcid_id = record.get("orcid-identifier", {}).get("path", "")
                    if orcid_id:
                        profile = self._get_profile_details(orcid_id, access_token)
                        if profile:
                            profiles.append(profile)
                
                time.sleep(self.rate_limit_delay)
                return profiles[:limit]
        
        except Exception as e:
            logger.error(f"Authenticated search failed: {str(e)}")
        
        return self._get_mock_profiles(job_titles, locations, limit) if self.use_mock_fallbacks else []
    
    def _get_access_token(self) -> Optional[str]:
        """Get OAuth2 access token for authenticated API access."""
        try:
            token_url = f"{self.base_url}/oauth/token"
            
            data = {
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "scope": "/read-public",
                "grant_type": "client_credentials"
            }
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"
            }
            
            response = requests.post(token_url, data=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                token_data = response.json()
                return token_data.get("access_token")
        
        except Exception as e:
            logger.error(f"Failed to get access token: {str(e)}")
        
        return None
    
    def _get_profile_details(self, orcid_id: str, access_token: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get detailed profile information for an ORCID ID.
        
        Args:
            orcid_id: ORCID identifier (e.g., "0000-0002-1825-0097")
            access_token: Optional access token for authenticated requests
        """
        try:
            url = f"{self.public_base_url}/v3.0/{orcid_id}/record"
            
            headers = {"Accept": "application/json"}
            if access_token:
                headers["Authorization"] = f"Bearer {access_token}"
                url = f"{self.base_url}/v3.0/{orcid_id}/record"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                record = response.json()
                return self._parse_orcid_record(record, orcid_id)
        
        except Exception as e:
            logger.warning(f"Failed to get profile details for {orcid_id}: {str(e)}")
        
        return None
    
    def _parse_orcid_record(self, record: Dict[str, Any], orcid_id: str) -> Dict[str, Any]:
        """Parse ORCID record into our standard profile format."""
        if not record:
            return None

        def _val(v: Any) -> str:
            if v is None:
                return ""
            if isinstance(v, str):
                return v
            if isinstance(v, dict):
                inner = v.get("value")
                if isinstance(inner, str):
                    return inner
                inner = v.get("content")
                if isinstance(inner, str):
                    return inner
            return ""
            
        person = record.get("person", {}) or {}
        activities = record.get("activities-summary", {}) or {}
        
        # Extract name
        name_parts = person.get("name", {}) or {}
        given_names = name_parts.get("given-names", {}) or {}
        family_name = name_parts.get("family-name", {}) or {}
        given_name = _val(given_names)
        family_name_value = _val(family_name)
        full_name = f"{given_name} {family_name_value}".strip()
        
        # Extract current employment
        employments_section = activities.get("employments", {}) or {}
        employments = employments_section.get("employment-summary", []) or []
        current_employment = employments[0] if employments else None
        
        # Extract organization
        organization_name = ""
        if current_employment:
            org = current_employment.get("organization", {}) or {}
            organization_name = _val(org.get("name")) or org.get("name", "")
        
        # Extract title/role
        title = ""
        if current_employment:
            title = _val(current_employment.get("role-title")) or current_employment.get("role-title", "")
        
        # Extract location from addresses
        location = ""
        addresses_section = person.get("addresses", {}) or {}
        addresses = addresses_section.get("address", []) or []
        if addresses:
            address = addresses[0] or {}
            city = _val(address.get("city")) or address.get("city", "")
            region = _val(address.get("region")) or address.get("region", "")
            country_section = address.get("country", {}) or {}
            country = _val(country_section) or country_section.get("value", "")
            location = ", ".join(filter(None, [city, region, country]))
        
        # Extract email
        emails_section = person.get("emails", {}) or {}
        emails = emails_section.get("email", []) or []
        email = ""
        if emails:
            email_obj = emails[0] or {}
            email = email_obj.get("email", "")
        
        # Extract keywords/research areas
        keywords = []
        keywords_section = person.get("keywords", {}) or {}
        keywords_list = keywords_section.get("keyword", []) or []
        for kw in keywords_list:
            if kw:
                keywords.append(_val(kw) or kw.get("content", ""))
        
        return {
            "name": full_name or "Unknown",
            "title": title or "Researcher",
            "company": organization_name or "Unknown",
            "location": location or "Unknown",
            "email": email,
            "orcid_id": orcid_id,
            "orcid_url": f"https://orcid.org/{orcid_id}",
            "keywords": keywords,
            "extracted_at": datetime.now().isoformat()
        }
    
    
    def enrich_profile(self, orcid_id: str) -> Dict[str, Any]:
        """
        Enrich a single ORCID profile with full details.
        
        Args:
            orcid_id: ORCID identifier
        
        Returns:
            Enriched profile dictionary
        """
        try:
            profile = self._get_profile_details(orcid_id, self._get_access_token() if self.client_id else None)
            if profile:
                profile["enriched"] = True
                return profile
            else:
                return {"orcid_id": orcid_id, "enriched": False}
        
        except Exception as e:
            logger.error(f"Error enriching profile {orcid_id}: {str(e)}")
            return {"orcid_id": orcid_id, "error": str(e)}


def search_orcid_profiles(
    job_titles: List[str],
    locations: Optional[List[str]] = None,
    affiliations: Optional[List[str]] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    limit: int = 100
) -> List[Dict[str, Any]]:
    """
    Convenience function to search ORCID profiles.
    
    Args:
        job_titles: List of job title keywords
        locations: Optional list of location keywords
        affiliations: Optional list of affiliation/organization keywords
        client_id: ORCID API client ID (optional)
        client_secret: ORCID API client secret (optional)
        limit: Maximum results
    
    Returns:
        List of profile dictionaries
    """
    scraper = ORCIDScraper(client_id=client_id, client_secret=client_secret)
    return scraper.search_profiles(job_titles, locations, affiliations, limit)


if __name__ == "__main__":
    # Test the scraper
    scraper = ORCIDScraper()
    results = scraper.search_profiles(
        job_titles=["toxicology", "researcher"],
        locations=["Cambridge", "Boston"],
        limit=10
    )
    print(f"Found {len(results)} profiles")
    for profile in results[:3]:
        print(f"- {profile['name']}: {profile['title']} at {profile['company']}")
        print(f"  ORCID: {profile.get('orcid_url', 'N/A')}")

