"""
Email Finder Module
Uses Hunter.io, Apollo.io, or Clearbit APIs to find and verify emails

This module discovers email addresses and verifies their validity.
"""

import requests
from typing import Dict, Any, Optional, List
import logging
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EmailFinder:
    """
    Email discovery and verification service.
    """
    
    def __init__(self, api_provider: str = "hunter", api_key: Optional[str] = None):
        """
        Initialize email finder.
        
        Args:
            api_provider: One of "hunter", "apollo", "clearbit"
            api_key: API key for the provider
        """
        self.api_provider = api_provider.lower()
        self.api_key = api_key
        self.base_urls = {
            "hunter": "https://api.hunter.io/v2",
            "apollo": "https://api.apollo.io/v1",
            "clearbit": "https://person.clearbit.com/v2"
        }
    
    def find_email(self, first_name: str, last_name: str, company_or_domain: str) -> Dict[str, Any]:
        """
        Find email address for a person.
        
        Args:
            first_name: First name
            last_name: Last name
            company_or_domain: Company name or domain
        
        Returns:
            Email information dictionary
        """
        # Extract domain if company_or_domain looks like a domain
        if "." in company_or_domain and not " " in company_or_domain:
            domain = company_or_domain
            company = None
        else:
            company = company_or_domain
            domain = self._extract_domain_from_company(company)
        
        try:
            if self.api_provider == "hunter":
                return self._find_hunter(first_name, last_name, domain)
            elif self.api_provider == "apollo":
                return self._find_apollo(first_name, last_name, company)
            elif self.api_provider == "clearbit":
                return self._find_clearbit(first_name, last_name, domain)
            elif self.api_provider == "pattern":
                return self._generate_email_patterns(first_name, last_name, domain or company)
            else:
                return self._generate_email_patterns(first_name, last_name, domain or company)
        
        except Exception as e:
            logger.error(f"Error finding email: {str(e)}")
            return self._generate_email_patterns(first_name, last_name, domain or company)
    
    def _find_hunter(
        self,
        first_name: str,
        last_name: str,
        domain: str
    ) -> Dict[str, Any]:
        """Find email using Hunter.io API."""
        if not self.api_key:
            logger.warning("No Hunter.io API key. No email found.")
            return {
                "email": "Not found",
                "confidence": 0,
                "verified": False,
                "source": "not_found",
                "patterns": []
            }
        
        try:
            url = f"{self.base_urls['hunter']}/email-finder"
            params = {
                "domain": domain,
                "first_name": first_name,
                "last_name": last_name,
                "api_key": self.api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get("data", {}).get("email"):
                email = data["data"]["email"]
                # Use actual confidence score from API if available
                confidence = data.get("data", {}).get("score", 85)
                # Get verification status from API
                verification_status = data.get("data", {}).get("sources", [])
                is_verified = len(verification_status) > 0
                
                # Verify email using Hunter's verify endpoint
                verify_result = self._verify_hunter_email(email)
                if verify_result.get("result") == "deliverable":
                    is_verified = True
                
                return {
                    "email": email,
                    "confidence": confidence,
                    "verified": is_verified,
                    "source": "hunter",
                    "patterns": [email],
                    "verification_details": verify_result
                }
            else:
                logger.info(f"Hunter.io found no email for {first_name} {last_name} at {domain}")
                return {
                    "email": "Not found",
                    "confidence": 0,
                    "verified": False,
                    "source": "not_found",
                    "patterns": []
                }
        
        except Exception as e:
            logger.error(f"Hunter.io API error: {str(e)}")
            return {
                "email": "Not found",
                "confidence": 0,
                "verified": False,
                "source": "not_found",
                "patterns": []
            }
    
    def _verify_hunter_email(self, email: str) -> Dict[str, Any]:
        """Verify email using Hunter.io email verifier API."""
        if not self.api_key:
            return {"result": "unknown", "reason": "no_api_key"}
        
        try:
            url = f"{self.base_urls['hunter']}/email-verifier"
            params = {
                "email": email,
                "api_key": self.api_key
            }
            
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            result_data = data.get("data", {})
            
            return {
                "result": result_data.get("result", "unknown"),
                "score": result_data.get("score", 0),
                "sources": result_data.get("sources", []),
                "disposable": result_data.get("disposable", False),
                "webmail": result_data.get("webmail", False)
            }
        
        except Exception as e:
            logger.warning(f"Hunter.io email verification error: {str(e)}")
            return {"result": "unknown", "reason": str(e)}
    
    def _find_apollo(
        self,
        first_name: str,
        last_name: str,
        company: str
    ) -> Dict[str, Any]:
        """Find email using Apollo.io API."""
        # Skip Apollo.io API calls due to authentication issues
        # Return not found instead of generating fake emails
        logger.info(f"No real email found for {first_name} {last_name} at {company} - Apollo.io API disabled")
        return {
            "email": "Not found",
            "confidence": 0,
            "verified": False,
            "source": "not_found",
            "patterns": []
        }
    
    def _find_clearbit(
        self,
        first_name: str,
        last_name: str,
        domain: str
    ) -> Dict[str, Any]:
        """Find email using Clearbit API."""
        # TODO: Implement Clearbit API calls
        # Return not found instead of generating fake emails
        logger.info(f"No real email found for {first_name} {last_name} at {domain} - Clearbit API not implemented")
        return {
            "email": "Not found",
            "confidence": 0,
            "verified": False,
            "source": "not_found",
            "patterns": []
        }
    
    def _generate_email_patterns(self, first_name: str, last_name: str, company_or_domain: str) -> Dict[str, Any]:
        """
        Generate email patterns - now returns 'not found' since we don't want fake emails.
        
        Args:
            first_name: First name
            last_name: Last name
            company_or_domain: Company name or domain
        
        Returns:
            Email information dictionary with 'not found' status
        """
        # Instead of generating fake emails, return not found
        logger.info(f"No real email found for {first_name} {last_name} at {company_or_domain}")
        return {
            "email": "Not found",
            "confidence": 0,
            "verified": False,
            "source": "not_found",
            "patterns": []
        }
    
    def verify_email(self, email: str, service: str = "hunter") -> Dict[str, Any]:
        """
        Verify email address validity.
        
        Args:
            email: Email address to verify
            service: Verification service ("hunter", "zerobounce", "neverbounce", "emailvalidator")
        
        Returns:
            Verification result dictionary
        """
        try:
            if service == "hunter" and self.api_provider == "hunter":
                verify_result = self._verify_hunter_email(email)
                return {
                    "valid": verify_result.get("result") == "deliverable",
                    "format_valid": True,
                    "disposable": verify_result.get("disposable", False),
                    "webmail": verify_result.get("webmail", False),
                    "score": verify_result.get("score", 0),
                    "source": "hunter",
                    "details": verify_result
                }
            elif service == "zerobounce":
                return self._verify_zerobounce(email)
            elif service == "neverbounce":
                return self._verify_neverbounce(email)
            else:
                return self._verify_basic(email)
        
        except Exception as e:
            logger.error(f"Error verifying email: {str(e)}")
            return {"valid": False, "error": str(e)}
    
    def _verify_zerobounce(self, email: str) -> Dict[str, Any]:
        """Verify email using ZeroBounce API."""
        if not self.api_key:
            return self._verify_basic(email)
        
        # TODO: Implement ZeroBounce API
        return self._verify_basic(email)
    
    def _verify_neverbounce(self, email: str) -> Dict[str, Any]:
        """Verify email using NeverBounce API."""
        if not self.api_key:
            return self._verify_basic(email)
        
        # TODO: Implement NeverBounce API
        return self._verify_basic(email)
    
    def _verify_basic(self, email: str) -> Dict[str, Any]:
        """Basic email format validation."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        is_valid_format = bool(re.match(pattern, email))
        
        return {
            "valid": is_valid_format,
            "format_valid": is_valid_format,
            "disposable": False,  # Would need API to check
            "source": "basic"
        }
    
    def find_email_for_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find email for a profile dictionary.
        
        Args:
            profile: Profile dictionary with name, company, etc.
        
        Returns:
            Email information dictionary
        """
        name = profile.get("name", "").strip()
        
        # Check if email already exists in profile
        existing_email = profile.get("email", "")
        if existing_email and existing_email != "Not found" and "@" in existing_email:
            return {
                "email": existing_email,
                "confidence": 90,
                "verified": False,
                "source": "orcid",
                "patterns": [existing_email]
            }
        
        # Extract first and last name with better handling
        name_parts = name.replace("Dr.", "").replace("PhD", "").replace("MD", "").replace("Prof.", "").strip().split()
        first_name = name_parts[0] if len(name_parts) > 0 else ""
        last_name = name_parts[-1] if len(name_parts) > 1 else ""
        
        # If we couldn't extract both names, return empty result
        if not first_name or not last_name:
            return {
                "email": "Not found",
                "confidence": 0,
                "verified": False,
                "source": "not_found",
                "patterns": []
            }
        
        # Get company and try to extract domain
        company = profile.get("company", "")
        affiliation = profile.get("affiliation", "")

        # Prefer an explicitly discovered domain (e.g., from company research)
        explicit_domain = (profile.get("company_domain") or "").strip()
        if explicit_domain:
            domain = explicit_domain
        else:
            domain = ""
        
        # Try to extract domain from affiliation first
        if not domain and affiliation:
            # Look for email domain in affiliation
            import re
            email_pattern = r'@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            matches = re.findall(email_pattern, affiliation)
            if matches:
                domain = matches[0]
        
        # If no domain from affiliation, try Serp API lookup (no heuristic guessing)
        if not domain:
            domain = self._extract_domain_from_company(company)
        
        if not domain:
            logger.debug(f"No domain found for company: {company}")
            return {
                "email": "Not found",
                "confidence": 0,
                "verified": False,
                "source": "not_found",
                "patterns": []
            }
        
        result = self.find_email(first_name, last_name, domain)
        # Store result in profile-compatible format
        return {
            "email": result.get("email"),
            "confidence": result.get("confidence", 0),
            "verified": result.get("verified", False),
            "source": result.get("source", "not_found"),
            "patterns": result.get("patterns", [])
        }
    
    def _extract_domain_from_company(self, company: str) -> str:
        """Extract domain from company name using Serp API or heuristics."""
        if not company or company == "Unknown":
            return ""
        
        # Try to extract domain from affiliation if available
        # (This would be passed from the profile)
        
        # Use Serp API to find company website if available
        try:
            from config import get_config
            config = get_config()
            serp_api_key = config.get("serp_api_key")
            
            if serp_api_key:
                try:
                    from serpapi import GoogleSearch
                    
                    # Search for company website
                    params = {
                        "q": f"{company} official website",
                        "api_key": serp_api_key,
                        "engine": "google",
                        "num": 1
                    }
                    
                    search = GoogleSearch(params)
                    results = search.get_dict()
                    
                    organic_results = results.get("organic_results", [])
                    if organic_results:
                        link = organic_results[0].get("link", "")
                        # Extract domain from URL
                        from urllib.parse import urlparse
                        parsed = urlparse(link)
                        domain = parsed.netloc
                        if domain:
                            # Remove www. prefix
                            domain = domain.replace("www.", "")
                            return domain
                except Exception as e:
                    logger.debug(f"Serp API domain lookup failed: {str(e)}")
        except ImportError:
            pass
        
        return ""


def find_email_for_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to find email for a profile.
    
    Args:
        profile: Profile dictionary with name, company, etc.
    
    Returns:
        Email information dictionary
    """
    from config import get_config
    config = get_config()
    finder = EmailFinder(
        api_provider=config.get('email_provider', 'apollo'),
        api_key=config.get('email_api_key')
    )
    
    name = profile.get("name", "").strip()
    # Extract first and last name
    name_parts = name.replace("Dr.", "").replace("PhD", "").strip().split()
    first_name = name_parts[0] if name_parts else ""
    last_name = name_parts[-1] if len(name_parts) > 1 else ""
    
    company = profile.get("company", "")
    
    result = finder.find_email(first_name, last_name, company)
    # Store result in profile-compatible format
    return {
        "email": result.get("email"),
        "email_confidence": result.get("confidence", 0),
        "email_verified": result.get("verified", False),
        "email_source": result.get("source", "pattern"),
        "email_patterns": result.get("patterns", [])
    }


if __name__ == "__main__":
    # Test the email finder
    finder = EmailFinder()
    result = finder.find_email("Sarah", "Chen", "NeuroTech Bio")
    print(f"Found email: {result.get('email')}")
    print(f"Confidence: {result.get('confidence')}%")
    print(f"Patterns: {result.get('patterns', [])[:3]}")

