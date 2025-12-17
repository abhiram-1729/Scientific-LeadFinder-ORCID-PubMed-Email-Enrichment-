#!/usr/bin/env python3
"""
Run Lead Generation Pipeline
Execute this script to run the complete lead generation pipeline with real APIs
"""

import sys
import os
from data_pipeline.main_pipeline import LeadGenerationPipeline
from config import get_config

def main():
    """Run the lead generation pipeline."""
    
    print("=" * 60)
    print("Lead Generation System - Real Data Only")
    print("=" * 60)
    print()
    
    # Load configuration
    print("Loading configuration...")
    config = get_config()
    
    # Check required API keys
    print("\nChecking API configuration...")
    missing_keys = []
    
    if not config.get("email_api_key"):
        missing_keys.append("EMAIL_API_KEY (Hunter API)")
    if not config.get("serp_api_key"):
        missing_keys.append("SERP_API_KEY")
    
    if missing_keys:
        print("⚠️  Warning: Missing API keys:")
        for key in missing_keys:
            print(f"   - {key}")
        print("\nSome features may not work without these keys.")
        print("See REAL_DATA_INTEGRATION_GUIDE.md for setup instructions.")
        print()
    
    # Initialize pipeline
    print("Initializing pipeline...")
    try:
        pipeline = LeadGenerationPipeline(config=config)
        print("✅ Pipeline initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing pipeline: {str(e)}")
        return 1
    
    # Define search criteria
    print("\n" + "=" * 60)
    print("Search Criteria")
    print("=" * 60)
    
    search_criteria = {
        "job_titles": ["toxicology", "safety", "director", "scientist"],
        "locations": ["Cambridge", "Boston", "San Francisco", "San Diego"],
        "pubmed_keywords": [
            "Drug-Induced Liver Injury",
            "3D cell culture",
            "hepatic spheroids",
            "organ-on-chip",
            "investigative toxicology"
        ],
        "conferences": ["SOT"],
        "limit": 50
    }
    
    print(f"Job Titles: {search_criteria['job_titles']}")
    print(f"Locations: {search_criteria['locations']}")
    print(f"PubMed Keywords: {search_criteria['pubmed_keywords']}")
    print(f"Limit: {search_criteria['limit']} profiles")
    print()
    
    # Run pipeline
    print("=" * 60)
    print("Running Pipeline")
    print("=" * 60)
    print()
    
    try:
        leads = pipeline.run_pipeline(
            search_criteria=search_criteria,
            enrich=True,
            score=True
        )
        
        print("\n" + "=" * 60)
        print("Results")
        print("=" * 60)
        print(f"Total leads generated: {len(leads)}")
        
        if leads:
            print("\nTop 10 Leads:")
            print("-" * 60)
            for i, lead in enumerate(leads[:10], 1):
                score = lead.get("score", {}).get("total_score", 0) if isinstance(lead.get("score"), dict) else lead.get("score", 0)
                name = lead.get("name", "Unknown")
                title = lead.get("title", "N/A")
                company = lead.get("company", "N/A")
                email = lead.get("email", "Not found")
                
                print(f"{i}. {name}")
                print(f"   Title: {title}")
                print(f"   Company: {company}")
                print(f"   Email: {email}")
                print(f"   Score: {score}")
                print()
            
            # Save results
            output_dir = config.get("output_dir", "output")
            os.makedirs(output_dir, exist_ok=True)
            
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = os.path.join(output_dir, f"leads_{timestamp}.csv")
            
            # Convert to DataFrame and save
            import pandas as pd
            
            # Flatten lead data for CSV
            leads_data = []
            for lead in leads:
                lead_row = {
                    "name": lead.get("name", ""),
                    "title": lead.get("title", ""),
                    "company": lead.get("company", ""),
                    "location": lead.get("location", ""),
                    "email": lead.get("email", "Not found"),
                    "score": lead.get("score", {}).get("total_score", 0) if isinstance(lead.get("score"), dict) else lead.get("score", 0),
                    "orcid_id": lead.get("orcid_id", ""),
                    "source": lead.get("source", "")
                }
                leads_data.append(lead_row)
            
            df = pd.DataFrame(leads_data)
            df = df.sort_values("score", ascending=False)
            df.to_csv(output_file, index=False)
            
            print(f"✅ Results saved to: {output_file}")
        else:
            print("\n⚠️  No leads found. This could mean:")
            print("   - APIs are not configured correctly")
            print("   - No matching profiles found")
            print("   - API errors occurred")
            print("\nCheck logs above for details.")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error running pipeline: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())



