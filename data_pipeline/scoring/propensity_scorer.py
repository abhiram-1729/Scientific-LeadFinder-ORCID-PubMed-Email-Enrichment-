"""
Real Data-Based Propensity Scoring System
Implements scoring algorithm (0-100 points) based on ACTUAL available data

This module calculates lead scores based on real data fields from ORCID, company research, etc.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PropensityScorer:
    """
    Calculates propensity scores for leads based on actual available data.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize scorer with configuration.
        
        Args:
            config: Optional custom scoring configuration
        """
        self.max_score = 100
        # Real scoring weights based on available data
        self.weights = {
            "title_relevance": 30,      # Job title relevance to toxicology/3D models
            "publication_count": 25,    # Number of publications (strong signal)
            "location_quality": 15,     # Location in biotech hubs
            "company_found": 10,        # Company information available
            "email_found": 10,          # Email address found
            "company_signals": 10       # Company research signals
        }
    
    def calculate_score(self, profile: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate comprehensive propensity score for a profile using REAL data.
        
        Args:
            profile: Profile dictionary with actual data fields
        
        Returns:
            Score breakdown dictionary
        """
        try:
            scores = {}
            total_score = 0
            
            # Title relevance score
            title_score = self._score_title_relevance(profile)
            scores["title_relevance"] = title_score
            total_score += title_score
            
            # Location quality score
            location_score = self._score_location_quality(profile)
            scores["location_quality"] = location_score
            total_score += location_score
            
            # Publication count score
            pub_score = self._score_publications(profile)
            scores["publication_count"] = pub_score
            total_score += pub_score
            
            # Company found score
            company_found_score = self._score_company_found(profile)
            scores["company_found"] = company_found_score
            total_score += company_found_score
            
            # Email found score
            email_score = self._score_email_found(profile)
            scores["email_found"] = email_score
            total_score += email_score
            
            # Company signals score
            company_score = self._score_company_signals(profile)
            scores["company_signals"] = company_score
            total_score += company_score
            
            # Cap at max score
            total_score = min(total_score, self.max_score)
            
            return {
                "total_score": total_score,
                "probability_score": total_score,
                "score_breakdown": scores,
                "scored_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Error calculating score: {str(e)}")
            return {
                "total_score": 0,
                "probability_score": 0,
                "error": str(e)
            }
    
    def _score_title_relevance(self, profile: Dict[str, Any]) -> int:
        """Score based on job title relevance to toxicology/3D models."""
        title = profile.get("title", "").lower()
        weight = self.weights["title_relevance"]
        
        if not title or title == "researcher" or title == "unknown":
            return 0
        
        # High relevance titles (full points)
        high_relevance = [
            "toxicology", "toxicologist", "safety", "drug safety", 
            "preclinical", "hepatic", "liver", "dili", "3d", "in vitro"
        ]
        
        # Medium relevance titles (half points)
        medium_relevance = [
            "director", "senior", "lead", "principal", "head",
            "phd", "md", "scientist", "research", "pharmacology"
        ]
        
        # Check for high relevance
        for keyword in high_relevance:
            if keyword in title:
                return weight
        
        # Check for medium relevance
        for keyword in medium_relevance:
            if keyword in title:
                return weight // 2
        
        return 0
    
    def _score_location_quality(self, profile: Dict[str, Any]) -> int:
        """Score based on location quality."""
        enriched_location = (profile.get("location_analysis") or {}).get("personal_location")
        location_raw = enriched_location or profile.get("location", "")
        location = (location_raw or "").lower()
        weight = self.weights["location_quality"]
        
        if not location or location == "unknown":
            return 0
        
        # Top biotech hubs (full points)
        top_hubs = ["cambridge", "boston", "san francisco", "bay area", "san diego", "basel"]
        
        # Secondary tech areas (half points)
        secondary_hubs = ["new york", "seattle", "austin", "raleigh", "phoenix", "denver"]
        
        # Check top hubs
        for hub in top_hubs:
            if hub in location:
                return weight
        
        # Check secondary hubs
        for hub in secondary_hubs:
            if hub in location:
                return weight // 2
        
        return 0
    
    def _score_publications(self, profile: Dict[str, Any]) -> int:
        """Score based on publication count and relevance."""
        publications = profile.get("publications", [])
        weight = self.weights["publication_count"]
        
        if not publications:
            return 0
        
        # Count publications
        pub_count = len(publications)
        
        # Check for relevant keywords in publication titles
        relevant_keywords = ["dili", "liver", "3d", "organoid", "spheroid", "toxicology", "hepatic", "in vitro"]
        relevant_count = 0
        
        for pub in publications:
            title = pub.get("title", "").lower()
            if any(keyword in title for keyword in relevant_keywords):
                relevant_count += 1
        
        # Base score on count
        base_score = 0
        if pub_count >= 10:
            base_score = weight
        elif pub_count >= 5:
            base_score = weight * 3 // 4
        elif pub_count >= 2:
            base_score = weight // 2
        else:
            base_score = weight // 4
        
        # Bonus for relevant publications
        if relevant_count > 0:
            relevance_bonus = min(relevant_count * 3, weight // 4)
            return min(base_score + relevance_bonus, weight)
        
        return base_score
    
    def _score_company_found(self, profile: Dict[str, Any]) -> int:
        """Score based on whether company information is available."""
        company = profile.get("company", "")
        weight = self.weights["company_found"]
        
        if not company or company == "Unknown":
            return 0
        
        # Bonus if company source is known (pubmed, orcid, etc.)
        company_source = profile.get("company_source", "")
        if company_source:
            return weight
        
        # Still give points if company is found
        return weight // 2
    
    def _score_email_found(self, profile: Dict[str, Any]) -> int:
        """Score based on whether email is found."""
        email = profile.get("email", "")
        email_confidence = profile.get("email_confidence", 0)
        weight = self.weights["email_found"]
        
        if not email or email == "Not found" or email == "":
            return 0
        
        # Score based on confidence
        if email_confidence >= 80:
            return weight
        elif email_confidence >= 50:
            return weight * 3 // 4
        elif email_confidence > 0:
            return weight // 2
        
        # Email found but no confidence score
        return weight // 2
    
    def _score_company_signals(self, profile: Dict[str, Any]) -> int:
        """Score based on company research signals."""
        company_research = profile.get("company_research", {})
        weight = self.weights["company_signals"]
        
        if not company_research:
            return 0
        
        score = 0
        
        # Check if company uses 3D models
        if company_research.get("uses_3d_models"):
            score += weight // 2
        
        # Check relevant technologies
        relevant_tech = company_research.get("relevant_technologies", [])
        if relevant_tech:
            score += weight // 4
        
        # Check job postings
        if company_research.get("job_postings_relevant"):
            score += weight // 4
        
        # Check if open to NAMs
        if company_research.get("open_to_nams"):
            score += weight // 4
        
        return min(score, weight)
    
    def _score_profile_completeness(self, profile: Dict[str, Any]) -> int:
        """Score based on profile completeness."""
        weight = self.weights["profile_completeness"]
        
        required_fields = ["name", "title", "company", "location"]
        optional_fields = ["email", "orcid_id", "keywords"]
        
        score = 0
        
        # Check required fields
        required_complete = 0
        for field in required_fields:
            value = profile.get(field, "")
            if value and value != "Unknown" and value != "":
                required_complete += 1
        
        # Score based on required field completion
        if required_complete == 4:
            score += weight // 2
        elif required_complete >= 2:
            score += weight // 4
        
        # Check optional fields
        optional_complete = 0
        for field in optional_fields:
            value = profile.get(field, "")
            if value and value != "":
                optional_complete += 1
        
        # Add bonus for optional fields
        score += (optional_complete * weight) // 8
        
        return min(score, weight)
    
    def _score_keyword_match(self, profile: Dict[str, Any]) -> int:
        """Score based on research keyword relevance."""
        keywords = profile.get("keywords", [])
        weight = self.weights["keyword_match"]
        
        if not keywords:
            return 0
        
        # Relevant keywords for 3D models/toxicology
        relevant_keywords = [
            "toxicology", "3d", "in vitro", "organoid", "spheroid", 
            "liver", "hepatic", "dili", "microphysiological", "organ-on-chip",
            "drug", "safety", "preclinical"
        ]
        
        # Count matches
        matches = 0
        for keyword in keywords:
            keyword_lower = keyword.lower()
            for relevant in relevant_keywords:
                if relevant in keyword_lower:
                    matches += 1
                    break
        
        # Score based on matches
        if matches >= 3:
            return weight
        elif matches >= 2:
            return weight * 3 // 4
        elif matches >= 1:
            return weight // 2
        else:
            return 0


def score_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to score a profile.
    
    Args:
        profile: Profile dictionary
    
    Returns:
        Score dictionary
    """
    scorer = PropensityScorer()
    return scorer.calculate_score(profile)


if __name__ == "__main__":
    # Test the scorer with realistic data
    scorer = PropensityScorer()
    
    test_profile = {
        "name": "Dr. Sarah Chen",
        "title": "Director of Toxicology",
        "company": "NeuroTech Bio",
        "location": "Cambridge, MA",
        "publications": [
            {"title": "DILI study in 3D models", "pub_date": "2024-01-01"},
            {"title": "Liver toxicity assessment", "pub_date": "2023-06-15"}
        ],
        "company_research": {
            "uses_3d_models": True,
            "relevant_technologies": ["3D cell culture", "toxicology"],
            "open_to_nams": True
        },
        "keywords": ["toxicology", "3D models", "liver", "in vitro"],
        "orcid_id": "0000-0001-2345-6789",
        "email": "sarah.chen@neurotechbio.com"
    }
    
    result = scorer.calculate_score(test_profile)
    print(f"Total Score: {result['total_score']}")
    print(f"Breakdown: {result['score_breakdown']}")
