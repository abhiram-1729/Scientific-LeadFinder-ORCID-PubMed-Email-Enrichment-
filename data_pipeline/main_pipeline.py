"""
Main Data Pipeline
Orchestrates the entire lead generation process

This module coordinates scrapers, enrichment, and scoring.
"""

import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_config
from data_pipeline.scrapers.orcid_scraper import ORCIDScraper
from data_pipeline.scrapers.pubmed_scraper import PubMedScraper
from data_pipeline.scrapers.conference_scraper import ConferenceScraper
from data_pipeline.scrapers.funding_scraper import FundingScraper
from data_pipeline.enrichment.email_finder import EmailFinder
from data_pipeline.enrichment.location_analyzer import LocationAnalyzer
from data_pipeline.enrichment.company_research import CompanyResearcher
from data_pipeline.scoring.propensity_scorer import PropensityScorer
from data_pipeline.scoring.ranking_engine import RankingEngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LeadGenerationPipeline:
    """
    Main pipeline for lead generation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize pipeline with configuration.
        
        Args:
            config: Configuration dictionary with API keys, etc.
        """
        self.config = config or {}
        
        # Initialize scrapers
        self.orcid_scraper = ORCIDScraper(
            client_id=self.config.get("orcid_client_id"),
            client_secret=self.config.get("orcid_client_secret"),
            use_sandbox=self.config.get("orcid_use_sandbox", False)
        )
        self.pubmed_scraper = PubMedScraper(
            email=self.config.get("pubmed_email"),
            api_key=self.config.get("pubmed_api_key")
        )
        self.conference_scraper = ConferenceScraper()
        self.funding_scraper = FundingScraper(
            api_key=self.config.get("funding_api_key"),
            source=self.config.get("funding_source", "crunchbase")
        )
        
        # Initialize enrichment modules
        self.email_finder = EmailFinder(
            api_provider=self.config.get("email_provider", "hunter"),
            api_key=self.config.get("email_api_key")
        )
        self.location_analyzer = LocationAnalyzer(
            google_maps_api_key=self.config.get("google_maps_api_key")
        )
        self.company_researcher = CompanyResearcher(
            serp_api_key=self.config.get("serp_api_key"),
            serp_engine=self.config.get("serp_engine", "google")
        )
        
        # Initialize scoring
        self.scorer = PropensityScorer()
        self.ranker = RankingEngine()
    
    def run_pipeline(
        self,
        search_criteria: Dict[str, Any],
        enrich: bool = True,
        score: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Run the complete lead generation pipeline.
        
        Args:
            search_criteria: Search criteria dictionary
            enrich: Whether to enrich profiles
            score: Whether to score profiles
        
        Returns:
            List of enriched and scored leads
        """
        try:
            logger.info("Starting lead generation pipeline...")
            
            # Step 1: Find profiles from ORCID
            logger.info("Step 1: Finding ORCID profiles...")
            orcid_profiles = self.orcid_scraper.search_profiles(
                job_titles=search_criteria.get("job_titles", []),
                locations=search_criteria.get("locations", []),
                affiliations=search_criteria.get("affiliations", []),
                limit=search_criteria.get("limit", 100)
            )
            logger.info(f"Found {len(orcid_profiles)} ORCID profiles")
            
            # Step 2: Find publications from PubMed
            logger.info("Step 2: Searching PubMed...")
            pubmed_keywords = search_criteria.get("pubmed_keywords", [
                "Drug-Induced Liver Injury",
                "3D cell culture",
                "organ-on-chip"
            ])
            publications = self.pubmed_scraper.search_publications(
                keywords=pubmed_keywords,
                max_results=50
            )
            logger.info(f"Found {len(publications)} publications")
            
            # Step 3: Find conference presenters
            logger.info("Step 3: Searching conferences...")
            conferences = search_criteria.get("conferences", ["SOT", "AACR"])
            conference_presenters = self.conference_scraper.search_conference_presenters(
                conference=conferences[0] if conferences else "SOT",
                keywords=search_criteria.get("conference_keywords", ["toxicology", "3D models"]),
                year=search_criteria.get("year", 2024)
            )
            logger.info(f"Found {len(conference_presenters)} conference presenters")
            
            # Step 4: Combine and deduplicate profiles
            logger.info("Step 4: Combining data sources...")
            all_profiles = self._combine_profiles(
                orcid_profiles,
                publications,
                conference_presenters
            )
            logger.info(f"Total unique profiles: {len(all_profiles)}")
            
            # Step 5: Enrich profiles
            if enrich:
                logger.info("Step 5: Enriching profiles...")
                enriched_profiles = []
                for i, profile in enumerate(all_profiles, 1):
                    logger.info(f"Enriching profile {i}/{len(all_profiles)}: {profile.get('name', 'Unknown')}")
                    enriched = self._enrich_profile(profile)
                    enriched_profiles.append(enriched)
                all_profiles = enriched_profiles
            
            # Step 6: Score profiles
            if score:
                logger.info("Step 6: Scoring profiles...")
                scored_profiles = []
                for profile in all_profiles:
                    score_result = self.scorer.calculate_score(profile)
                    profile["score"] = score_result
                    scored_profiles.append(profile)
                all_profiles = scored_profiles
            
            # Step 7: Rank profiles
            logger.info("Step 7: Ranking profiles...")
            ranked_profiles = self.ranker.rank_leads(all_profiles, sort_by="score")
            
            logger.info(f"Pipeline complete! Generated {len(ranked_profiles)} leads")
            return ranked_profiles
        
        except Exception as e:
            logger.error(f"Error in pipeline: {str(e)}")
            raise
    
    def _combine_profiles(
        self,
        orcid_profiles: List[Dict],
        publications: List[Dict],
        conference_presenters: List[Dict]
    ) -> List[Dict]:
        """Combine profiles from different sources."""
        # Start with ORCID profiles
        combined = {}
        for profile in orcid_profiles:
            name = profile.get("name", "").strip()
            if name:
                combined[name] = profile.copy()

        # Fallback: enrich ORCID profiles with empty fields from PubMed author search
        for name, profile in combined.items():
            if (profile.get("title") == "Researcher" or not profile.get("title")) or \
               profile.get("company") == "Unknown" or \
               profile.get("location") == "Unknown":
                # Search PubMed for this author to get affiliation/organization
                author_pubs = self.pubmed_scraper.find_author_publications(name, max_results=5)
                if author_pubs:
                    # Extract organization and affiliation from first publication
                    first_pub = author_pubs[0]
                    org = first_pub.get("organization", "").strip()
                    aff = first_pub.get("corresponding_affiliation", "").strip()

                    if org and profile.get("company") == "Unknown":
                        profile["company"] = org
                        profile["company_source"] = "pubmed_fallback"

                    if aff:
                        profile["affiliation"] = aff
                        loc = self._extract_location_from_affiliation(aff)
                        if loc and loc != "Unknown" and profile.get("location") == "Unknown":
                            profile["location"] = loc
                
                # Second fallback: use SerpAPI to search for researcher and find company/location
                if profile.get("company") == "Unknown" or profile.get("location") == "Unknown":
                    serp_info = self._search_researcher_via_serp(name)
                    if serp_info:
                        if serp_info.get("company") and profile.get("company") == "Unknown":
                            profile["company"] = serp_info["company"]
                            profile["company_source"] = "serp_fallback"
                        if serp_info.get("location") and profile.get("location") == "Unknown":
                            profile["location"] = serp_info["location"]
                        if serp_info.get("affiliation"):
                            profile["affiliation"] = serp_info["affiliation"]
        
        # Add publication data and extract company/affiliation info
        for pub in publications:
            author = pub.get("corresponding_author", "").strip()
            organization = pub.get("organization", "").strip()
            affiliation = pub.get("corresponding_affiliation", "").strip()
            
            # Try to match author by name (fuzzy matching)
            matched_name = None
            for name in combined.keys():
                # Simple name matching - check if author name contains profile name or vice versa
                if author and name:
                    author_parts = set(author.lower().split())
                    name_parts = set(name.lower().split())
                    # If significant overlap, consider it a match
                    if len(author_parts & name_parts) >= 2:
                        matched_name = name
                        break
            
            if matched_name:
                profile = combined[matched_name]
                if "publications" not in profile:
                    profile["publications"] = []
                profile["publications"].append(pub)
                
                # Update company if missing or "Unknown"
                if (not profile.get("company") or profile.get("company") == "Unknown") and organization:
                    profile["company"] = organization
                    profile["company_source"] = "pubmed"
                
                # Store affiliation for domain extraction
                if affiliation:
                    profile["affiliation"] = affiliation
            else:
                # Create new profile from publication if author not in ORCID
                if author:
                    new_profile = {
                        "name": author,
                        "title": "Researcher",
                        "company": organization or "Unknown",
                        "location": self._extract_location_from_affiliation(affiliation),
                        "email": "",
                        "orcid_id": "",
                        "publications": [pub],
                        "affiliation": affiliation,
                        "source": "pubmed",
                        "company_source": "pubmed" if organization else ""
                    }
                    combined[author] = new_profile
        
        # Add conference data
        for presenter in conference_presenters:
            name = presenter.get("name", "").strip()
            if name in combined:
                if "conference_activity" not in combined[name]:
                    combined[name]["conference_activity"] = []
                combined[name]["conference_activity"].append(presenter)
                
                # Update company from conference if missing
                if (not combined[name].get("company") or combined[name].get("company") == "Unknown"):
                    conf_company = presenter.get("affiliation", "")
                    if conf_company:
                        combined[name]["company"] = conf_company
                        combined[name]["company_source"] = "conference"
        
        return list(combined.values())
    
    def _extract_location_from_affiliation(self, affiliation: str) -> str:
        """Extract location from affiliation string."""
        if not affiliation:
            return "Unknown"
        
        # Look for city, state/country patterns
        parts = affiliation.split(",")
        if len(parts) >= 2:
            # Usually location is in last parts
            location_parts = [p.strip() for p in parts[-2:]]
            return ", ".join(location_parts)
        
        return "Unknown"
    
    def _enrich_profile(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich a single profile with all enrichment modules."""
        # First, try to improve company information if missing
        company = profile.get("company", "")
        if not company or company == "Unknown":
            # Try to extract from affiliation
            affiliation = profile.get("affiliation", "")
            if affiliation:
                company = self._extract_company_from_affiliation(affiliation)
                if company:
                    profile["company"] = company
                    profile["company_source"] = profile.get("company_source", "affiliation")

        # Research company first (used to discover official website/domain)
        if company and company != "Unknown":
            company_info = self.company_researcher.research_company(
                company_name=company,
                company_description=profile.get("affiliation", "")
            )
            profile["company_research"] = company_info
            profile["company_domain"] = company_info.get("company_domain", "")
            profile["company_website"] = company_info.get("company_website", "")

            # Get funding data
            funding_info = self.funding_scraper.search_company_funding(
                company_name=company
            )
            profile["funding"] = funding_info
        else:
            profile["company_research"] = {}
            profile["funding"] = {}
            profile["company_domain"] = ""
            profile["company_website"] = ""

        # Analyze location and write normalized location back to the profile
        location_info = self.location_analyzer.analyze_location(
            personal_location=profile.get("location"),
            company_location=profile.get("company_location"),
            company_name=profile.get("company")
        )
        profile["location_analysis"] = location_info
        normalized_location = (location_info or {}).get("personal_location")
        if normalized_location and normalized_location != "Unknown":
            profile["location"] = normalized_location

        # Find email (requires a real domain; EmailFinder now avoids heuristic guessing)
        # EmailFinder will use profile["company_domain"] if available
        email_info = self.email_finder.find_email_for_profile(profile)
        profile["email"] = email_info.get("email")
        profile["email_confidence"] = email_info.get("confidence", 0)
        profile["email_verified"] = email_info.get("verified", False)
        profile["email_source"] = email_info.get("source", "not_found")
        
        return profile
    
    def _search_researcher_via_serp(self, researcher_name: str) -> Dict[str, Any]:
        """
        Search for researcher via SerpAPI to find company/location/affiliation.
        
        Args:
            researcher_name: Name of the researcher
        
        Returns:
            Dictionary with company, location, affiliation if found
        """
        try:
            if not self.config.get("serp_api_key"):
                return {}
            
            try:
                from serpapi import GoogleSearch
            except ImportError:
                logger.warning("SerpAPI library not installed. Skipping researcher search.")
                return {}
            
            # Search for researcher name + "researcher" to find their affiliation
            query = f'"{researcher_name}" researcher'
            params = {
                "q": query,
                "api_key": self.config.get("serp_api_key"),
                "engine": "google",
                "num": 5
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            organic_results = results.get("organic_results", [])
            
            if not organic_results:
                return {}
            
            # Extract company and location from first result snippet
            first_result = organic_results[0]
            snippet = first_result.get("snippet", "").lower()
            title = first_result.get("title", "").lower()
            combined_text = f"{title} {snippet}"
            
            company = ""
            location = ""
            affiliation = first_result.get("snippet", "")
            
            # Try to extract company name from snippet
            # Look for patterns like "at Company", "Company researcher", etc.
            import re
            at_pattern = r'at\s+([A-Z][A-Za-z\s&]+?)(?:\s+in\s+|,|\.|$)'
            at_match = re.search(at_pattern, affiliation)
            if at_match:
                company = at_match.group(1).strip()
            
            # Try to extract location from snippet
            # Look for city, state patterns
            location_pattern = r'(?:in|based in|located in)\s+([A-Z][A-Za-z\s,]+?)(?:\.|,|$)'
            loc_match = re.search(location_pattern, affiliation)
            if loc_match:
                location = loc_match.group(1).strip()
            
            import time
            time.sleep(1.0)
            
            return {
                "company": company,
                "location": location,
                "affiliation": affiliation,
                "source": "serp_researcher_search"
            }
        
        except Exception as e:
            logger.debug(f"SerpAPI researcher search failed for {researcher_name}: {str(e)}")
            return {}

    def _extract_company_from_affiliation(self, affiliation: str) -> str:
        """Extract company/organization name from affiliation string."""
        if not affiliation:
            return ""
        
        # Use the same logic as PubMed scraper
        from data_pipeline.scrapers.pubmed_scraper import PubMedScraper
        scraper = PubMedScraper()
        return scraper._extract_organization_from_affiliation(affiliation)


def run_lead_generation(
    search_criteria: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Convenience function to run the lead generation pipeline.
    
    Args:
        search_criteria: Search criteria
        config: Optional configuration
    
    Returns:
        List of leads
    """
    pipeline = LeadGenerationPipeline(config=config)
    return pipeline.run_pipeline(search_criteria)


if __name__ == "__main__":
    # Example usage using full configuration (env + config.py)
    config = get_config()
    search_criteria = {
        "job_titles": ["toxicology", "safety", "director"],
        "locations": ["Cambridge", "Boston", "San Francisco"],
        "pubmed_keywords": ["Drug-Induced Liver Injury", "3D cell culture"],
        "conferences": ["SOT"],
        "limit": 10
    }
    
    pipeline = LeadGenerationPipeline(config=config)
    leads = pipeline.run_pipeline(search_criteria)
    
    print(f"\nGenerated {len(leads)} leads:")
    for lead in leads[:5]:
        score = lead.get("score", {}).get("total_score", 0)
        print(f"  {lead.get('name')}: {lead.get('title')} - Score: {score}")

