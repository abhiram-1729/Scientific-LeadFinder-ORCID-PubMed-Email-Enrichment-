"""
Company Research Module
Researches companies to determine if they use 3D models and relevant technologies

This module analyzes company information for technographic signals.
Uses Serp API for web searches and Google Scholar searches.
"""

import requests
from typing import Dict, Any, Optional, List
import logging
import re
import time
from urllib.parse import urlparse

# Try to import Serp API
try:
    from serpapi import GoogleSearch
    SERP_API_AVAILABLE = True
except ImportError:
    SERP_API_AVAILABLE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if not SERP_API_AVAILABLE:
    logger.warning("Serp API library not installed. Install with: pip install google-search-results")


class CompanyResearcher:
    """
    Researches companies for technographic and intent signals.
    Uses Serp API for web searches and Google Scholar searches.
    """
    
    def __init__(self, serp_api_key: Optional[str] = None, serp_engine: str = "google"):
        """
        Initialize company researcher.
        
        Args:
            serp_api_key: Serp API key for Google searches
            serp_engine: Search engine to use ("google", "scholar", "news")
        """
        self.serp_api_key = serp_api_key
        self.serp_engine = serp_engine
        self.relevant_keywords = [
            "3d cell culture",
            "organ-on-chip",
            "organoid",
            "spheroid",
            "in vitro model",
            "hepatic model",
            "drug safety",
            "toxicology",
            "NAMs",  # New Approach Methodologies
            "microphysiological"
        ]
    
    def research_company(
        self,
        company_name: str,
        company_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Research a company for relevant technology usage.
        
        Args:
            company_name: Company name
            company_description: Optional company description
        
        Returns:
            Company research dictionary
        """
        try:
            # Check description for keywords
            uses_3d_models = False
            relevant_technologies = []
            
            if company_description:
                description_lower = company_description.lower()
                for keyword in self.relevant_keywords:
                    if keyword.lower() in description_lower:
                        uses_3d_models = True
                        relevant_technologies.append(keyword)

            # Discover official website/domain (used for accurate email finding)
            website_info = self._find_company_website(company_name)
            
            # Check job postings using Serp API
            job_postings = self._check_job_postings(company_name)
            
            # Check company website using Serp API
            website_content = self._check_website(company_name)
            
            # Search Google Scholar for company publications
            scholar_results = self._search_scholar(company_name)
            
            # Determine intent score
            intent_score = self._calculate_intent_score(
                uses_3d_models,
                relevant_technologies,
                job_postings,
                website_content,
                scholar_results
            )
            
            return {
                "company": company_name,
                "company_domain": website_info.get("domain", ""),
                "company_website": website_info.get("website", ""),
                "uses_3d_models": uses_3d_models,
                "relevant_technologies": relevant_technologies,
                "job_postings_relevant": job_postings.get("has_relevant", False),
                "job_postings_count": job_postings.get("count", 0),
                "website_mentions": website_content.get("mentions", []),
                "scholar_publications": scholar_results.get("publications", []),
                "scholar_count": scholar_results.get("count", 0),
                "intent_score": intent_score,
                "open_to_nams": intent_score > 50,
                "research_date": None  # Would be datetime.now()
            }
        
        except Exception as e:
            logger.error(f"Error researching company {company_name}: {str(e)}")
            return {
                "company": company_name,
                "error": str(e)
            }

    def _find_company_website(self, company_name: str) -> Dict[str, str]:
        """Find the official company website and domain using Serp API."""
        if not SERP_API_AVAILABLE or not self.serp_api_key:
            return {"website": "", "domain": "", "source": "not_configured"}

        try:
            params = {
                "q": f"{company_name} official website",
                "api_key": self.serp_api_key,
                "engine": "google",
                "num": 3
            }

            search = GoogleSearch(params)
            results = search.get_dict()
            organic_results = results.get("organic_results", [])
            if not organic_results:
                return {"website": "", "domain": "", "source": "serp_api"}

            link = organic_results[0].get("link", "")
            if not link:
                return {"website": "", "domain": "", "source": "serp_api"}

            parsed = urlparse(link)
            domain = (parsed.netloc or "").replace("www.", "")

            time.sleep(1.0)
            return {
                "website": link,
                "domain": domain,
                "source": "serp_api"
            }
        except Exception as e:
            logger.debug(f"Company website lookup failed: {str(e)}")
            return {"website": "", "domain": "", "source": "error"}
    
    def _check_job_postings(self, company_name: str) -> Dict[str, Any]:
        """
        Check if company has relevant job postings using Serp API.
        
        Searches Google for job postings related to the company and relevant keywords.
        """
        if not SERP_API_AVAILABLE or not self.serp_api_key:
            logger.warning("Serp API not available. Cannot check job postings.")
            return {"has_relevant": False, "count": 0, "error": "Serp API not configured"}
        
        try:
            # Build search query for job postings
            keywords_query = " OR ".join(self.relevant_keywords[:3])  # Use top 3 keywords
            query = f"{company_name} jobs {keywords_query}"
            
            params = {
                "q": query,
                "api_key": self.serp_api_key,
                "engine": "google",
                "num": 10,
                "tbm": "nws"  # News search can find job announcements
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Check organic results for job-related content
            organic_results = results.get("organic_results", [])
            job_count = 0
            has_relevant = False
            
            for result in organic_results:
                title = result.get("title", "").lower()
                snippet = result.get("snippet", "").lower()
                combined_text = f"{title} {snippet}"
                
                # Check if it's job-related
                if any(term in combined_text for term in ["job", "career", "hiring", "position", "opening"]):
                    job_count += 1
                    # Check if relevant keywords are mentioned
                    if any(keyword.lower() in combined_text for keyword in self.relevant_keywords):
                        has_relevant = True
            
            # Rate limiting
            time.sleep(1.0)
            
            return {
                "has_relevant": has_relevant,
                "count": job_count,
                "source": "serp_api"
            }
        
        except Exception as e:
            logger.error(f"Error checking job postings with Serp API: {str(e)}")
            return {"has_relevant": False, "count": 0, "error": str(e)}
    
    def _check_website(self, company_name: str) -> Dict[str, Any]:
        """
        Check company website for relevant mentions using Serp API.
        
        Searches Google for company website and analyzes content for relevant keywords.
        """
        if not SERP_API_AVAILABLE or not self.serp_api_key:
            logger.warning("Serp API not available. Cannot check website content.")
            return {"mentions": [], "error": "Serp API not configured"}
        
        try:
            # Search for company website
            query = f"{company_name} site:{company_name.lower().replace(' ', '')}.com"
            
            params = {
                "q": query,
                "api_key": self.serp_api_key,
                "engine": "google",
                "num": 5
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Extract mentions from search results
            mentions = []
            organic_results = results.get("organic_results", [])
            
            for result in organic_results:
                title = result.get("title", "")
                snippet = result.get("snippet", "")
                combined_text = f"{title} {snippet}".lower()
                
                # Check for relevant keywords
                for keyword in self.relevant_keywords:
                    if keyword.lower() in combined_text and keyword not in mentions:
                        mentions.append(keyword)
            
            # Also do a general search about the company
            general_query = f"{company_name} {' '.join(self.relevant_keywords[:3])}"
            params_general = {
                "q": general_query,
                "api_key": self.serp_api_key,
                "engine": "google",
                "num": 5
            }
            
            search_general = GoogleSearch(params_general)
            results_general = search_general.get_dict()
            
            for result in results_general.get("organic_results", []):
                snippet = result.get("snippet", "").lower()
                for keyword in self.relevant_keywords:
                    if keyword.lower() in snippet and keyword not in mentions:
                        mentions.append(keyword)
            
            # Rate limiting
            time.sleep(1.0)
            
            return {
                "mentions": mentions,
                "source": "serp_api"
            }
        
        except Exception as e:
            logger.error(f"Error checking website with Serp API: {str(e)}")
            return {"mentions": [], "error": str(e)}
    
    def _search_scholar(self, company_name: str) -> Dict[str, Any]:
        """
        Search Google Scholar for company publications using Serp API.
        
        Args:
            company_name: Company name to search for
        
        Returns:
            Dictionary with publications and count
        """
        if not SERP_API_AVAILABLE or not self.serp_api_key:
            return {"publications": [], "count": 0}
        
        try:
            # Build search query with company name and relevant keywords
            keywords_query = " OR ".join(self.relevant_keywords[:3])
            query = f"{company_name} {keywords_query}"
            
            params = {
                "q": query,
                "api_key": self.serp_api_key,
                "engine": "google_scholar",
                "num": 10
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            publications = []
            organic_results = results.get("organic_results", [])
            
            for result in organic_results:
                publication = {
                    "title": result.get("title", ""),
                    "authors": result.get("publication_info", {}).get("authors", []),
                    "link": result.get("link", ""),
                    "snippet": result.get("snippet", "")
                }
                publications.append(publication)
            
            # Rate limiting
            time.sleep(1.0)
            
            return {
                "publications": publications,
                "count": len(publications),
                "source": "serp_api_scholar"
            }
        
        except Exception as e:
            logger.error(f"Error searching Google Scholar with Serp API: {str(e)}")
            return {"publications": [], "count": 0, "error": str(e)}
    
    def _calculate_intent_score(
        self,
        uses_3d_models: bool,
        technologies: List[str],
        job_postings: Dict[str, Any],
        website_content: Dict[str, Any],
        scholar_results: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Calculate company intent score (0-100).
        
        Scoring:
        - Uses 3D models: +40
        - Each relevant technology: +10
        - Relevant job postings: +20
        - Website mentions: +10 each
        - Scholar publications: +5 each (up to +20)
        """
        score = 0
        
        if uses_3d_models:
            score += 40
        
        score += len(technologies) * 10
        
        if job_postings.get("has_relevant"):
            score += 20
        
        score += len(website_content.get("mentions", [])) * 10
        
        # Add scholar publications score
        if scholar_results:
            scholar_count = scholar_results.get("count", 0)
            score += min(scholar_count * 5, 20)  # Max 20 points for publications
        
        return min(score, 100)


def research_company_for_profile(profile: Dict[str, Any], serp_api_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Convenience function to research company for a profile.
    
    Args:
        profile: Profile dictionary
        serp_api_key: Optional Serp API key
    
    Returns:
        Company research results
    """
    researcher = CompanyResearcher(serp_api_key=serp_api_key)
    return researcher.research_company(
        company_name=profile.get("company", ""),
        company_description=profile.get("company_description")
    )


if __name__ == "__main__":
    # Test the company researcher
    researcher = CompanyResearcher()
    result = researcher.research_company("NeuroTech Bio", "Biotech company focused on 3D cell culture models")
    print(f"Company: {result.get('company')}")
    print(f"Uses 3D Models: {result.get('uses_3d_models')}")
    print(f"Intent Score: {result.get('intent_score')}")

