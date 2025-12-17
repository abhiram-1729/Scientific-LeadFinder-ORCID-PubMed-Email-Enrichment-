"""
PubMed API Scraper
Fetches scientific publications from PubMed/NCBI

This module searches PubMed for relevant publications and extracts author information.
"""

import requests
import time
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
import xml.etree.ElementTree as ET

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PubMedScraper:
    """
    PubMed/NCBI API scraper for scientific publications.
    """
    
    def __init__(self, email: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize PubMed scraper.
        
        Args:
            email: Email for NCBI API (recommended but not required)
            api_key: NCBI API key (optional, increases rate limit)
        """
        self.email = email or "your-email@example.com"
        self.api_key = api_key
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
        self.rate_limit_delay = 0.34  # NCBI requires 3 requests/second max
    
    def search_publications(
        self,
        keywords: List[str],
        max_results: int = 100,
        date_range_days: int = 730  # Last 2 years
    ) -> List[Dict[str, Any]]:
        """
        Search PubMed for publications matching keywords.
        
        Args:
            keywords: List of search keywords
            max_results: Maximum number of results
            date_range_days: Number of days to look back
        
        Returns:
            List of publication dictionaries
        """
        try:
            # Build search query
            query = " OR ".join(keywords)
            date_cutoff = (datetime.now() - timedelta(days=date_range_days)).strftime("%Y/%m/%d")
            query += f" AND {date_cutoff}:{datetime.now().strftime('%Y/%m/%d')}[Publication Date]"
            
            # Search PubMed
            search_url = f"{self.base_url}/esearch.fcgi"
            params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "email": self.email
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            logger.info(f"Searching PubMed with query: {query}")
            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            
            search_data = response.json()
            pmids = search_data.get("esearchresult", {}).get("idlist", [])
            
            if not pmids:
                # Retry without date restriction (often too strict for niche keywords)
                retry_query = " OR ".join(keywords)
                params["term"] = retry_query
                logger.info(f"No results with date filter. Retrying PubMed with query: {retry_query}")

                time.sleep(self.rate_limit_delay)
                retry_response = requests.get(search_url, params=params, timeout=10)
                retry_response.raise_for_status()
                retry_data = retry_response.json()
                pmids = retry_data.get("esearchresult", {}).get("idlist", [])

                if not pmids:
                    logger.info("No publications found.")
                    return []
            
            # Fetch detailed publication data
            publications = self._fetch_publication_details(pmids[:max_results])
            
            logger.info(f"Found {len(publications)} publications")
            return publications
        
        except Exception as e:
            logger.error(f"Error searching PubMed: {str(e)}")
            logger.error("PubMed API error - returning empty results. Check API connectivity and credentials.")
            return []
    
    def _fetch_publication_details(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """Fetch detailed information for a list of PubMed IDs."""
        if not pmids:
            return []
        
        try:
            # Fetch full XML data to get affiliations
            fetch_url = f"{self.base_url}/efetch.fcgi"
            params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "xml",
                "rettype": "abstract",
                "email": self.email
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            time.sleep(self.rate_limit_delay)
            response = requests.get(fetch_url, params=params)
            response.raise_for_status()
            
            # Parse XML to extract affiliations
            import xml.etree.ElementTree as ET
            try:
                root = ET.fromstring(response.content)
            except ET.ParseError as e:
                logger.warning(f"XML parsing error, falling back to summaries: {str(e)}")
                return self._fetch_publication_summaries(pmids)
            
            publications = []
            
            # Handle namespaces
            namespaces = {
                '': 'http://www.ncbi.nlm.nih.gov/pubmed'
            }
            
            for article in root.findall(".//PubmedArticle", namespaces):
                pmid_elem = article.find(".//PMID")
                pmid = pmid_elem.text if pmid_elem is not None else ""
                
                title_elem = article.find(".//ArticleTitle")
                title = title_elem.text if title_elem is not None else ""
                
                # Extract authors with affiliations
                authors_list = []
                affiliations_list = []
                
                for author in article.findall(".//Author"):
                    last_name = author.find("LastName")
                    first_name = author.find("ForeName")
                    if last_name is not None and first_name is not None:
                        author_name = f"{first_name.text} {last_name.text}"
                        authors_list.append(author_name)
                        
                        # Extract affiliation
                        affiliation_elem = author.find(".//Affiliation")
                        if affiliation_elem is not None and affiliation_elem.text:
                            affiliations_list.append(affiliation_elem.text)
                
                # Also get affiliations from article
                for affil in article.findall(".//Affiliation"):
                    if affil.text and affil.text not in affiliations_list:
                        affiliations_list.append(affil.text)
                
                # Extract journal
                journal_elem = article.find(".//Journal/Title")
                journal = journal_elem.text if journal_elem is not None else ""
                
                # Extract publication date
                pub_date_elem = article.find(".//PubDate/Year")
                pub_date = pub_date_elem.text if pub_date_elem is not None else ""
                
                # Extract corresponding author (usually last author)
                corresponding_author = authors_list[-1] if authors_list else ""
                corresponding_affiliation = affiliations_list[-1] if affiliations_list else ""
                
                # Extract organization from affiliation
                organization = self._extract_organization_from_affiliation(corresponding_affiliation)
                
                pub = {
                    "pmid": pmid,
                    "title": title,
                    "authors": authors_list,
                    "affiliations": affiliations_list,
                    "corresponding_author": corresponding_author,
                    "corresponding_affiliation": corresponding_affiliation,
                    "organization": organization,
                    "journal": journal,
                    "pub_date": pub_date,
                    "doi": "",
                    "abstract": ""
                }
                publications.append(pub)
            
            return publications
        
        except Exception as e:
            logger.error(f"Error fetching publication details: {str(e)}")
            # Fallback to summary if XML fails
            return self._fetch_publication_summaries(pmids)
    
    def _fetch_publication_summaries(self, pmids: List[str]) -> List[Dict[str, Any]]:
        """Fallback: Fetch summaries when XML fetch fails."""
        try:
            fetch_url = f"{self.base_url}/esummary.fcgi"
            params = {
                "db": "pubmed",
                "id": ",".join(pmids),
                "retmode": "json",
                "email": self.email
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            time.sleep(self.rate_limit_delay)
            response = requests.get(fetch_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            publications = []
            
            for pmid, details in data.get("result", {}).items():
                if pmid == "uids":
                    continue
                
                # Try to extract organization from authors if available
                authors = details.get("authors", [])
                organization = ""
                affiliation = ""
                
                # Look for affiliation in author data
                if isinstance(authors, list) and authors:
                    last_author = authors[-1]
                    if isinstance(last_author, dict):
                        # Some summary formats include affiliation
                        affiliation = last_author.get("affiliation", "")
                        if affiliation:
                            organization = self._extract_organization_from_affiliation(affiliation)
                
                pub = {
                    "pmid": pmid,
                    "title": details.get("title", ""),
                    "authors": authors,
                    "journal": details.get("source", ""),
                    "pub_date": details.get("pubdate", ""),
                    "doi": details.get("elocationid", ""),
                    "corresponding_author": self._extract_corresponding_author(details),
                    "corresponding_affiliation": affiliation,
                    "organization": organization,
                    "affiliations": [affiliation] if affiliation else []
                }
                publications.append(pub)
            
            return publications
        except Exception as e:
            logger.error(f"Error fetching summaries: {str(e)}")
            return []
    
    def _extract_organization_from_affiliation(self, affiliation: str) -> str:
        """Extract organization name from affiliation string."""
        if not affiliation:
            return ""
        
        # Common patterns: "Department of X, University Name" or "Company Name, City"
        # Try to extract the main organization
        parts = affiliation.split(",")
        if len(parts) >= 2:
            # Usually organization is in first or second part
            for part in parts[:3]:
                part = part.strip()
                # Skip common prefixes
                if any(prefix in part.lower() for prefix in ["department", "school", "college", "institute", "center"]):
                    continue
                # Look for university or company indicators
                if any(indicator in part.lower() for indicator in ["university", "college", "institute", "hospital", "medical", "pharma", "biotech", "labs", "inc", "llc"]):
                    return part
                # If it's a substantial name (more than 3 words), it might be the org
                if len(part.split()) <= 4 and len(part) > 5:
                    return part
        
        # Fallback: return first substantial part
        if parts:
            return parts[0].strip()
        
        return ""
    
    def _extract_corresponding_author(self, details: Dict) -> Optional[str]:
        """Extract corresponding author from publication details."""
        authors = details.get("authors", [])
        if isinstance(authors, list) and len(authors) > 0:
            # Typically last author is corresponding author
            last_author = authors[-1] if isinstance(authors[-1], dict) else {"name": str(authors[-1])}
            return last_author.get("name", "")
        return None
    
    
    def find_author_publications(
        self,
        author_name: str,
        affiliation: Optional[str] = None,
        max_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Find publications by a specific author.
        
        Args:
            author_name: Author's name
            affiliation: Optional affiliation filter
            max_results: Maximum results
        
        Returns:
            List of publications
        """
        try:
            query = f'"{author_name}"[Author]'
            if affiliation:
                query += f' AND "{affiliation}"[Affiliation]'
            
            search_url = f"{self.base_url}/esearch.fcgi"
            params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json",
                "email": self.email
            }
            
            if self.api_key:
                params["api_key"] = self.api_key
            
            response = requests.get(search_url, params=params)
            response.raise_for_status()
            
            search_data = response.json()
            pmids = search_data.get("esearchresult", {}).get("idlist", [])
            
            if pmids:
                return self._fetch_publication_details(pmids)
            
            return []
        
        except Exception as e:
            logger.error(f"Error finding author publications: {str(e)}")
            return []


def search_pubmed(
    keywords: List[str],
    max_results: int = 100,
    date_range_days: int = 730
) -> List[Dict[str, Any]]:
    """
    Convenience function to search PubMed.
    
    Args:
        keywords: Search keywords
        max_results: Maximum results
        date_range_days: Days to look back
    
    Returns:
        List of publications
    """
    scraper = PubMedScraper()
    return scraper.search_publications(keywords, max_results, date_range_days)


if __name__ == "__main__":
    # Test the scraper
    scraper = PubMedScraper()
    results = scraper.search_publications(
        keywords=["Drug-Induced Liver Injury", "3D cell culture", "organ-on-chip"],
        max_results=5
    )
    print(f"Found {len(results)} publications")
    for pub in results:
        print(f"- {pub['title'][:80]}... by {pub.get('corresponding_author', 'Unknown')}")

