"""
Lead Generation System for 3D In-Vitro Models in Drug Safety Testing
Phase 1: Profile Finding and Scoring System

This module provides functionality to:
- Find profiles based on search criteria
- Calculate relevance scores
- Generate CSV reports
"""

import pandas as pd
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
import os


# Configuration parameters
CONFIG = {
    "scoring_weights": {
        "title_keywords": 30,  # Score for title containing "toxicology" or "safety"
        "biotech_hub": 15,     # Score for company in biotech hub
        "recent_publication": 40  # Score for recent publication
    },
    "biotech_hubs": [
        "Cambridge, MA",
        "San Francisco, CA",
        "San Diego, CA",
        "Boston, MA",
        "Research Triangle Park, NC",
        "Seattle, WA",
        "New York, NY"
    ],
    "title_keywords": ["toxicology", "safety", "drug safety", "safety assessment"],
    "output_dir": "output"
}


# Note: This module is deprecated. Use data_pipeline.main_pipeline instead.
# All mock data has been removed. System now uses only real APIs.


def find_profiles(search_criteria: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Find profiles matching the search criteria.
    
    Args:
        search_criteria: Dictionary containing:
            - job_titles: List of job title keywords to search for
            - locations: List of location keywords to search for
    
    Returns:
        List of matching profiles
    """
    try:
        matching_profiles = []
        job_titles = search_criteria.get("job_titles", [])
        locations = search_criteria.get("locations", [])
        
        # Convert to lowercase for case-insensitive matching
        job_titles_lower = [title.lower() for title in job_titles] if job_titles else []
        locations_lower = [loc.lower() for loc in locations] if locations else []
        
        # Note: This function is deprecated. Use data_pipeline.main_pipeline instead.
        # All mock data has been removed.
        profiles = []
        for profile in profiles:
            match = False
            
            # Check job title match
            if job_titles_lower:
                profile_title_lower = profile["title"].lower()
                if any(keyword in profile_title_lower for keyword in job_titles_lower):
                    match = True
            else:
                match = True  # If no title filter, include all
            
            # Check location match
            if locations_lower and match:
                profile_location_lower = profile["location"].lower()
                if not any(loc in profile_location_lower for loc in locations_lower):
                    match = False
            
            if match:
                matching_profiles.append(profile)
        
        return matching_profiles
    
    except Exception as e:
        print(f"Error finding profiles: {str(e)}")
        return []


def calculate_score(profile: Dict[str, Any]) -> int:
    """
    Calculate relevance score for a profile based on configurable weights.
    
    Scoring criteria:
    - Title contains "toxicology" or "safety": +30 points
    - Company location in biotech hub: +15 points
    - Recent publication (has publications): +40 points
    
    Args:
        profile: Profile dictionary
    
    Returns:
        Integer score (0-100+)
    """
    try:
        score = 0
        
        # Check title keywords
        title_lower = profile.get("title", "").lower()
        if any(keyword in title_lower for keyword in CONFIG["title_keywords"]):
            score += CONFIG["scoring_weights"]["title_keywords"]
        
        # Check biotech hub location
        location = profile.get("location", "")
        if location in CONFIG["biotech_hubs"]:
            score += CONFIG["scoring_weights"]["biotech_hub"]
        
        # Check for recent publications
        publications = profile.get("publications", [])
        if publications and len(publications) > 0:
            score += CONFIG["scoring_weights"]["recent_publication"]
        
        return score
    
    except Exception as e:
        print(f"Error calculating score for profile {profile.get('name', 'Unknown')}: {str(e)}")
        return 0


def generate_report(profiles: List[Dict[str, Any]], output_filename: Optional[str] = None) -> str:
    """
    Generate a CSV report from profiles with scores.
    
    Args:
        profiles: List of profile dictionaries
        output_filename: Optional custom filename (default: auto-generated)
    
    Returns:
        Path to the generated CSV file
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(CONFIG["output_dir"], exist_ok=True)
        
        # Calculate scores for all profiles
        scored_profiles = []
        for profile in profiles:
            score = calculate_score(profile)
            scored_profiles.append({
                "Name": profile.get("name", ""),
                "Title": profile.get("title", ""),
                "Company": profile.get("company", ""),
                "Location": profile.get("location", ""),
                "Score": score,
                "Email": profile.get("email", ""),
                "LinkedIn": profile.get("linkedin", ""),
                "Publications": "; ".join(profile.get("publications", [])),
                "Funding Status": profile.get("funding_status", ""),
                "Conference Activity": "; ".join(profile.get("conference_activity", []))
            })
        
        # Sort by score (descending)
        scored_profiles.sort(key=lambda x: x["Score"], reverse=True)
        
        # Create DataFrame
        df = pd.DataFrame(scored_profiles)
        
        # Generate filename if not provided
        if output_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"lead_report_{timestamp}.csv"
        
        # Ensure filename ends with .csv
        if not output_filename.endswith(".csv"):
            output_filename += ".csv"
        
        # Full path
        output_path = os.path.join(CONFIG["output_dir"], output_filename)
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        
        print(f"Report generated successfully: {output_path}")
        print(f"Total profiles: {len(scored_profiles)}")
        print(f"Average score: {df['Score'].mean():.2f}")
        print(f"Max score: {df['Score'].max()}")
        print(f"Min score: {df['Score'].min()}")
        
        return output_path
    
    except Exception as e:
        print(f"Error generating report: {str(e)}")
        raise


def main():
    """
    Main function to demonstrate the lead generation system.
    """
    print("=" * 60)
    print("Lead Generation System for 3D In-Vitro Models")
    print("=" * 60)
    
    # Example search criteria
    search_criteria = {
        "job_titles": ["toxicology", "safety", "director", "scientist"],
        "locations": ["Cambridge", "Boston", "San Francisco", "San Diego"]
    }
    
    print("\nSearch Criteria:")
    print(f"  Job Titles: {search_criteria['job_titles']}")
    print(f"  Locations: {search_criteria['locations']}")
    
    # Find matching profiles
    print("\nFinding matching profiles...")
    matching_profiles = find_profiles(search_criteria)
    print(f"Found {len(matching_profiles)} matching profiles")
    
    # Generate report
    print("\nGenerating report...")
    report_path = generate_report(matching_profiles)
    
    print(f"\nReport saved to: {report_path}")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()

