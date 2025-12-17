"""
Funding Data Scraper
Fetches funding information from NIH RePORTER (US) and CORDIS (EU)

This module extracts company funding data and grant information.
Uses only real, public APIs - no mock data.
"""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FundingScraper:
    """
    Scraper for funding data from various sources.
    """
    
    def __init__(self, api_key: Optional[str] = None, source: str = "nih_reporter"):
        """
        Initialize funding scraper.
        
        Args:
            api_key: API key (not required for NIH RePORTER or CORDIS)
            source: One of "nih_reporter", "cordis"
        """
        self.api_key = api_key
        self.source = source.lower()
        self.rate_limit_delay = 1.0
    
    def search_company_funding(
        self,
        company_name: str,
        keywords: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Search for funding information for a company.
        
        Args:
            company_name: Company name to search for
            keywords: Optional keywords to filter by
        
        Returns:
            Funding information dictionary
        """
        try:
            if self.source == "nih_reporter":
                return self._search_nih_reporter(company_name, keywords)
            elif self.source == "cordis":
                return self._search_cordis(company_name, keywords)
            else:
                logger.warning(f"Unknown funding source: {self.source}. Using NIH RePORTER.")
                return self._search_nih_reporter(company_name, keywords)
        
        except Exception as e:
            logger.error(f"Error searching funding data: {str(e)}")
            return {
                "company": company_name,
                "grants": [],
                "total_grants": 0,
                "source": self.source,
                "error": str(e)
            }
    
    def _search_cordis(
        self,
        company_name: str,
        keywords: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Search CORDIS API for EU grant data."""
        try:
            # CORDIS API endpoint (EU Horizon grants)
            url = "https://data.europa.eu/api/hub/search"
            params = {
                "q": company_name,
                "fq": "type:project",
                "rows": 10
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            grants = []
            
            for result in data.get("result", {}).get("results", []):
                grant = {
                    "grant_id": result.get("id", ""),
                    "title": result.get("title", ""),
                    "organization": company_name,
                    "amount": result.get("totalCost", 0),
                    "start_date": result.get("startDate", ""),
                    "end_date": result.get("endDate", ""),
                    "agency": "EU Horizon",
                    "programme": result.get("programme", "")
                }
                grants.append(grant)
            
            return {
                "company": company_name,
                "grants": grants,
                "total_grants": len(grants),
                "source": "CORDIS"
            }
        
        except Exception as e:
            logger.error(f"Error searching CORDIS: {str(e)}")
            return {
                "company": company_name,
                "grants": [],
                "total_grants": 0,
                "source": "CORDIS",
                "error": str(e)
            }
    
    def _search_nih_reporter(
        self,
        company_name: str,
        keywords: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Search NIH RePORTER for grant data."""
        # NIH RePORTER has a public API
        try:
            url = "https://api.reporter.nih.gov/v2/projects/search"
            payload = {
                "criteria": {
                    "org_names": [company_name]
                },
                "offset": 0,
                "limit": 10
            }
            
            response = requests.post(url, json=payload)
            response.raise_for_status()
            
            data = response.json()
            grants = []
            
            for project in data.get("results", []):
                grant = {
                    "grant_id": project.get("project_num", ""),
                    "title": project.get("project_title", ""),
                    "pi_name": project.get("contact_pi_name", ""),
                    "organization": project.get("organization", {}).get("org_name", ""),
                    "amount": project.get("award_amount", 0),
                    "start_date": project.get("project_start_date", ""),
                    "end_date": project.get("project_end_date", ""),
                    "agency": "NIH"
                }
                grants.append(grant)
            
            return {
                "company": company_name,
                "grants": grants,
                "total_grants": len(grants),
                "source": "NIH RePORTER"
            }
        
        except Exception as e:
            logger.error(f"Error searching NIH RePORTER: {str(e)}")
            return {
                "company": company_name,
                "grants": [],
                "total_grants": 0,
                "source": "NIH RePORTER",
                "error": str(e)
            }
    
    def search_recent_funding(
        self,
        keywords: List[str],
        days_back: int = 365,
        min_amount: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for recent funding/grant rounds matching keywords.
        
        Args:
            keywords: Keywords to search for
            days_back: Number of days to look back
            min_amount: Minimum funding amount
        
        Returns:
            List of funding/grant rounds
        """
        try:
            # Search NIH RePORTER for recent grants
            cutoff_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
            
            url = "https://api.reporter.nih.gov/v2/projects/search"
            payload = {
                "criteria": {
                    "text_words": keywords,
                    "project_start_date": {
                        "from_date": cutoff_date
                    }
                },
                "offset": 0,
                "limit": 100
            }
            
            response = requests.post(url, json=payload, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            grants = []
            
            for project in data.get("results", []):
                amount = project.get("award_amount", 0)
                if min_amount and amount < min_amount:
                    continue
                
                grant = {
                    "company": project.get("organization", {}).get("org_name", ""),
                    "grant_id": project.get("project_num", ""),
                    "title": project.get("project_title", ""),
                    "amount": amount,
                    "date": project.get("project_start_date", ""),
                    "pi_name": project.get("contact_pi_name", ""),
                    "agency": "NIH"
                }
                grants.append(grant)
            
            return grants
        
        except Exception as e:
            logger.error(f"Error searching recent funding: {str(e)}")
            return []


def get_company_funding(
    company_name: str,
    source: str = "nih_reporter",
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convenience function to get company funding data.
    
    Args:
        company_name: Company name
        source: Funding source
        api_key: API key
    
    Returns:
        Funding information
    """
    scraper = FundingScraper(api_key=api_key, source=source)
    return scraper.search_company_funding(company_name)


if __name__ == "__main__":
    # Test the scraper
    scraper = FundingScraper()
    funding = scraper.search_company_funding("NeuroTech Bio")
    print(f"Funding data for NeuroTech Bio:")
    print(f"  Latest round: {funding.get('latest_round')}")
    print(f"  Amount: ${funding.get('amount'):,}")

