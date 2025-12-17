"""
Streamlit Dashboard for Lead Generation System
Real-Data Scientific BD Intelligence Agent

This dashboard allows users to:
- Run the lead generation pipeline
- View and filter leads
- Analyze results
- Export data
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import sys

# Ensure project root is on sys.path so `import data_pipeline` works when
# running `streamlit run data_pipeline/dashboard/streamlit_dashboard.py`.
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from data_pipeline.main_pipeline import LeadGenerationPipeline
from config import get_config

# Page configuration
st.set_page_config(
    page_title="Lead Generation Dashboard - Real Data",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)


@st.cache_data(ttl=3600)  # Cache for 1 hour
def run_pipeline_cached(search_criteria, config):
    """Run pipeline with caching."""
    try:
        pipeline = LeadGenerationPipeline(config=config)
        leads = pipeline.run_pipeline(
            search_criteria=search_criteria,
            enrich=True,
            score=True
        )
        return leads
    except Exception as e:
        st.error(f"Pipeline error: {str(e)}")
        return []


def leads_to_dataframe(leads):
    """Convert leads list to DataFrame."""
    if not leads:
        return pd.DataFrame()
    
    leads_data = []
    for lead in leads:
        score = lead.get("score", {})
        if isinstance(score, dict):
            total_score = score.get("total_score", 0)
        else:
            total_score = score or 0

        location_analysis = lead.get("location_analysis", {}) if isinstance(lead.get("location_analysis"), dict) else {}
        normalized_location = location_analysis.get("personal_location") or lead.get("location", "")
        is_biotech_hub = location_analysis.get("is_biotech_hub")
        biotech_hub_name = location_analysis.get("biotech_hub_name")
        
        lead_row = {
            "Name": lead.get("name", ""),
            "Title": lead.get("title", ""),
            "Company": lead.get("company", ""),
            "Location": normalized_location,
            "Email": lead.get("email", "Not found"),
            "Score": total_score,
            "ORCID ID": lead.get("orcid_id", ""),
            "ORCID URL": lead.get("orcid_url", ""),
            "Source": lead.get("source", ""),
            "Email Confidence": lead.get("email_confidence", 0),
            "Email Verified": lead.get("email_verified", False),
            "Email Source": lead.get("email_source", ""),
            "Company Domain": lead.get("company_domain", "") or (lead.get("company_research", {}) or {}).get("company_domain", ""),
            "Company Website": lead.get("company_website", "") or (lead.get("company_research", {}) or {}).get("company_website", ""),
            "Biotech Hub": is_biotech_hub,
            "Biotech Hub Name": biotech_hub_name
        }
        leads_data.append(lead_row)
    
    return pd.DataFrame(leads_data)


def display_statistics(df: pd.DataFrame):
    """Display statistics about leads."""
    if df.empty:
        st.warning("No data to display statistics.")
        return
    
    st.subheader("📊 Statistics")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Leads", len(df))
    
    with col2:
        avg_score = df["Score"].mean() if "Score" in df.columns else 0
        st.metric("Average Score", f"{avg_score:.1f}")
    
    with col3:
        max_score = df["Score"].max() if "Score" in df.columns else 0
        st.metric("Max Score", int(max_score))
    
    with col4:
        emails_found = len(df[df["Email"] != "Not found"]) if "Email" in df.columns else 0
        st.metric("Emails Found", emails_found)


def display_charts(df: pd.DataFrame):
    """Display visualization charts."""
    if df.empty:
        return
    
    st.subheader("📈 Visualizations")
    
    if "Score" in df.columns:
        col1, col2 = st.columns(2)
        
        with col1:
            fig_hist = px.histogram(
                df,
                x="Score",
                nbins=20,
                title="Score Distribution",
                labels={"Score": "Lead Score", "count": "Number of Leads"}
            )
            st.plotly_chart(fig_hist, use_container_width=True)
        
        with col2:
            if "Location" in df.columns and len(df["Location"].unique()) > 1:
                location_counts = df["Location"].value_counts().head(10)
                fig_bar = px.bar(
                    x=location_counts.values,
                    y=location_counts.index,
                    orientation='h',
                    title="Leads by Location (Top 10)",
                    labels={"x": "Number of Leads", "y": "Location"}
                )
                st.plotly_chart(fig_bar, use_container_width=True)
            else:
                fig_box = px.box(
                    df,
                    y="Score",
                    title="Score Distribution (Box Plot)"
                )
                st.plotly_chart(fig_box, use_container_width=True)


def main():
    """Main dashboard function."""
    st.title("🔬 Lead Generation Dashboard")
    st.markdown("**Real-Data Scientific BD Intelligence Agent**")
    st.markdown("---")
    
    # Sidebar
    st.sidebar.header("⚙️ Configuration")
    
    # Load config
    config = get_config()
    
    # Check API keys
    st.sidebar.subheader("🔑 API Status")
    api_status = {}
    
    if config.get("email_api_key"):
        st.sidebar.success("✅ Hunter API configured")
        api_status["hunter"] = True
    else:
        st.sidebar.warning("⚠️ Hunter API key missing")
        api_status["hunter"] = False
    
    if config.get("serp_api_key"):
        st.sidebar.success("✅ Serp API configured")
        api_status["serp"] = True
    else:
        st.sidebar.warning("⚠️ Serp API key missing")
        api_status["serp"] = False
    
    if config.get("orcid_client_id"):
        st.sidebar.success("✅ ORCID API configured")
        api_status["orcid"] = True
    else:
        st.sidebar.info("ℹ️ ORCID API (optional)")
        api_status["orcid"] = False
    
    # Search criteria
    st.sidebar.subheader("🔍 Search Criteria")
    
    job_titles = st.sidebar.text_input(
        "Job Titles (comma-separated)",
        value="toxicology, safety, director, scientist",
        help="Enter job title keywords separated by commas"
    )
    
    locations = st.sidebar.text_input(
        "Locations (comma-separated)",
        value="Cambridge, Boston, San Francisco, San Diego",
        help="Enter location keywords separated by commas"
    )
    
    pubmed_keywords = st.sidebar.text_area(
        "PubMed Keywords (one per line)",
        value="Drug-Induced Liver Injury\n3D cell culture\nhepatic spheroids\norgan-on-chip",
        help="Enter PubMed search keywords, one per line"
    )
    
    limit = st.sidebar.slider(
        "Max Results",
        min_value=10,
        max_value=500,
        value=50,
        step=10,
        help="Maximum number of leads to generate"
    )
    
    # Filters
    st.sidebar.subheader("📊 Filters")
    min_score = st.sidebar.slider(
        "Minimum Score",
        min_value=0,
        max_value=100,
        value=0,
        step=5
    )
    
    filter_has_email = st.sidebar.checkbox(
        "Only show leads with email found",
        value=False,
        help="Filter to only leads where email was successfully found"
    )
    
    filter_has_company = st.sidebar.checkbox(
        "Only show leads with company found",
        value=False,
        help="Filter to only leads where company is not 'Unknown'"
    )
    
    filter_has_location = st.sidebar.checkbox(
        "Only show leads with location found",
        value=False,
        help="Filter to only leads where location is not 'Unknown'"
    )
    
    filter_biotech_hub = st.sidebar.checkbox(
        "Only show leads in biotech hubs",
        value=False,
        help="Filter to only leads located in biotech hub cities"
    )
    
    # Run button
    st.sidebar.markdown("---")
    run_button = st.sidebar.button("🚀 Run Pipeline", type="primary", use_container_width=True)
    
    # Main content
    if run_button:
        with st.spinner("Running pipeline... This may take a few minutes."):
            # Prepare search criteria
            search_criteria = {
                "job_titles": [t.strip() for t in job_titles.split(",") if t.strip()],
                "locations": [l.strip() for l in locations.split(",") if l.strip()],
                "pubmed_keywords": [k.strip() for k in pubmed_keywords.split("\n") if k.strip()],
                "limit": limit
            }
            
            # Run pipeline
            leads = run_pipeline_cached(search_criteria, config)
            
            if leads:
                # Convert to DataFrame
                df = leads_to_dataframe(leads)
                
                # Store in session state
                st.session_state['leads_df'] = df
                st.session_state['search_criteria'] = search_criteria
                
                st.success(f"✅ Pipeline completed! Found {len(leads)} leads")
            else:
                st.error("❌ No leads found. Check API configuration and try again.")
                st.info("💡 Tip: Make sure you have API keys configured in your .env file")
    
    # Display results if available
    if 'leads_df' in st.session_state and not st.session_state['leads_df'].empty:
        df = st.session_state['leads_df']
        
        # Apply filters
        filtered_df = df[df["Score"] >= min_score].copy()
        
        if filter_has_email:
            filtered_df = filtered_df[filtered_df["Email"] != "Not found"].copy()
        
        if filter_has_company:
            filtered_df = filtered_df[filtered_df["Company"] != "Unknown"].copy()
        
        if filter_has_location:
            filtered_df = filtered_df[filtered_df["Location"] != "Unknown"].copy()
        
        if filter_biotech_hub:
            filtered_df = filtered_df[filtered_df["Biotech Hub"] == True].copy()
        
        # Display statistics
        display_statistics(filtered_df)
        st.markdown("---")
        
        # Display charts
        display_charts(filtered_df)
        st.markdown("---")
        
        # Display data table
        st.subheader("📋 Lead Data")
        filter_summary = [f"score >= {min_score}"]
        if filter_has_email:
            filter_summary.append("email found")
        if filter_has_company:
            filter_summary.append("company found")
        if filter_has_location:
            filter_summary.append("location found")
        if filter_biotech_hub:
            filter_summary.append("biotech hub")
        
        filter_text = ", ".join(filter_summary)
        st.write(f"Showing {len(filtered_df)} of {len(df)} leads (filtered by: {filter_text})")
        
        st.dataframe(
            filtered_df.sort_values("Score", ascending=False),
            use_container_width=True,
            height=400
        )
        
        # Download button
        st.markdown("---")
        csv = filtered_df.to_csv(index=False)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"leads_{timestamp}.csv"
        
        st.download_button(
            label="📥 Download Filtered Data (CSV)",
            data=csv,
            file_name=filename,
            mime="text/csv",
            use_container_width=True
        )
    
    else:
        # Instructions
        st.info("👆 Configure your search criteria in the sidebar and click 'Run Pipeline' to start.")
        
        st.markdown("### 📝 How to Use")
        st.write("""
        1. **Configure APIs**: Make sure API keys are set in `.env` file
        2. **Set Search Criteria**: Use the sidebar to configure:
           - Job titles to search for
           - Locations to filter by
           - PubMed keywords for publication search
           - Maximum number of results
        3. **Run Pipeline**: Click "Run Pipeline" button
        4. **View Results**: Explore statistics, charts, and data table
        5. **Filter & Export**: Adjust filters and download results
        
        **Note**: The pipeline uses real APIs only - no mock data.
        """)
        
        # API setup instructions
        with st.expander("🔧 API Setup Instructions"):
            st.write("""
            **Required APIs:**
            - Hunter API (email finding)
            - Serp API (company research)
            
            **Optional APIs:**
            - ORCID API (researcher profiles)
            - PubMed API (publications)
            - Google Maps API (geocoding)
            
            See `REAL_DATA_INTEGRATION_GUIDE.md` for detailed setup instructions.
            """)


if __name__ == "__main__":
    main()

