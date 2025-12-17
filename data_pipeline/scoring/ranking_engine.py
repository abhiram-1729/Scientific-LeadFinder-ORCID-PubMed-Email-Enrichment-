"""
Ranking Engine
Ranks leads by score and additional criteria

This module handles lead ranking and prioritization.
"""

from typing import List, Dict, Any, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RankingEngine:
    """
    Ranks and prioritizes leads.
    """
    
    def __init__(self):
        """Initialize ranking engine."""
        pass
    
    def rank_leads(
        self,
        leads: List[Dict[str, Any]],
        sort_by: str = "score",
        ascending: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Rank leads by specified criteria.
        
        Args:
            leads: List of lead dictionaries
            sort_by: Field to sort by ("score", "name", "company", "location")
            ascending: Sort order
        
        Returns:
            Ranked list of leads
        """
        try:
            # Add rank to each lead
            ranked_leads = []
            
            # Sort leads
            if sort_by == "score":
                sorted_leads = sorted(
                    leads,
                    key=lambda x: x.get("score", {}).get("total_score", 0),
                    reverse=not ascending
                )
            elif sort_by == "name":
                sorted_leads = sorted(
                    leads,
                    key=lambda x: x.get("name", "").lower(),
                    reverse=ascending
                )
            elif sort_by == "company":
                sorted_leads = sorted(
                    leads,
                    key=lambda x: x.get("company", "").lower(),
                    reverse=ascending
                )
            elif sort_by == "location":
                sorted_leads = sorted(
                    leads,
                    key=lambda x: x.get("location_analysis", {}).get("personal_location", ""),
                    reverse=ascending
                )
            else:
                sorted_leads = leads
            
            # Add rank number
            for rank, lead in enumerate(sorted_leads, start=1):
                lead["rank"] = rank
                ranked_leads.append(lead)
            
            return ranked_leads
        
        except Exception as e:
            logger.error(f"Error ranking leads: {str(e)}")
            return leads
    
    def filter_by_score(
        self,
        leads: List[Dict[str, Any]],
        min_score: int = 0,
        max_score: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Filter leads by score range.
        
        Args:
            leads: List of leads
            min_score: Minimum score
            max_score: Maximum score
        
        Returns:
            Filtered leads
        """
        filtered = []
        for lead in leads:
            score = lead.get("score", {}).get("total_score", 0)
            if min_score <= score <= max_score:
                filtered.append(lead)
        
        return filtered
    
    def get_top_leads(
        self,
        leads: List[Dict[str, Any]],
        top_n: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get top N leads by score.
        
        Args:
            leads: List of leads
            top_n: Number of top leads to return
        
        Returns:
            Top N leads
        """
        ranked = self.rank_leads(leads, sort_by="score")
        return ranked[:top_n]


def rank_profiles(profiles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convenience function to rank profiles.
    
    Args:
        profiles: List of profile dictionaries
    
    Returns:
        Ranked profiles
    """
    engine = RankingEngine()
    return engine.rank_leads(profiles)


if __name__ == "__main__":
    # Test the ranking engine
    engine = RankingEngine()
    
    test_leads = [
        {"name": "A", "score": {"total_score": 85}},
        {"name": "B", "score": {"total_score": 70}},
        {"name": "C", "score": {"total_score": 95}}
    ]
    
    ranked = engine.rank_leads(test_leads)
    for lead in ranked:
        print(f"Rank {lead['rank']}: {lead['name']} - Score: {lead['score']['total_score']}")

