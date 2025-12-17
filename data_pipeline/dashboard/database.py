"""
Database Module
SQLite database for storing leads and tracking status

This module handles database operations for the lead generation system.
"""

import sqlite3
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LeadDatabase:
    """
    Database manager for leads.
    """
    
    def __init__(self, db_path: str = "leads.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Leads table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    title TEXT,
                    company TEXT,
                    personal_location TEXT,
                    company_hq TEXT,
                    email TEXT,
                    phone TEXT,
                    linkedin_url TEXT,
                    orcid_id TEXT,
                    orcid_url TEXT,
                    rank INTEGER,
                    probability_score REAL,
                    total_score REAL,
                    score_breakdown TEXT,
                    recent_publication TEXT,
                    company_funding TEXT,
                    conference_activity TEXT,
                    location_analysis TEXT,
                    company_research TEXT,
                    email_info TEXT,
                    status TEXT DEFAULT 'new',
                    notes TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name, company)
                )
            """)
            
            # Status tracking table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS lead_status (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    lead_id INTEGER,
                    status TEXT,
                    notes TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (lead_id) REFERENCES leads (id)
                )
            """)
            
            # Add ORCID columns if they don't exist (migration for existing databases)
            try:
                cursor.execute("ALTER TABLE leads ADD COLUMN orcid_id TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            try:
                cursor.execute("ALTER TABLE leads ADD COLUMN orcid_url TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            conn.commit()
            conn.close()
            logger.info("Database initialized successfully")
        
        except Exception as e:
            logger.error(f"Error initializing database: {str(e)}")
            raise
    
    def save_lead(self, lead: Dict[str, Any]) -> int:
        """
        Save or update a lead in the database.
        
        Args:
            lead: Lead dictionary
        
        Returns:
            Lead ID
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Extract data
            score_data = lead.get("score", {})
            location_data = lead.get("location_analysis", {})
            company_data = lead.get("company_research", {})
            email_data = lead.get("email_info", {})
            
            cursor.execute("""
                INSERT OR REPLACE INTO leads (
                    name, title, company, personal_location, company_hq,
                    email, phone, linkedin_url, orcid_id, orcid_url, rank, probability_score,
                    total_score, score_breakdown, recent_publication,
                    company_funding, conference_activity, location_analysis,
                    company_research, email_info, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lead.get("name"),
                lead.get("title"),
                lead.get("company"),
                location_data.get("personal_location"),
                location_data.get("company_hq"),
                lead.get("email"),
                lead.get("phone"),
                lead.get("linkedin_url"),  # Keep for backward compatibility
                lead.get("orcid_id"),
                lead.get("orcid_url"),
                lead.get("rank"),
                score_data.get("probability_score", 0),
                score_data.get("total_score", 0),
                json.dumps(score_data.get("score_breakdown", {})),
                json.dumps(lead.get("publications", [])),
                json.dumps(lead.get("funding", {})),
                json.dumps(lead.get("conference_activity", [])),
                json.dumps(location_data),
                json.dumps(company_data),
                json.dumps(email_data),
                lead.get("status", "new"),
                lead.get("notes", "")
            ))
            
            lead_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            logger.info(f"Saved lead: {lead.get('name')} (ID: {lead_id})")
            return lead_id
        
        except Exception as e:
            logger.error(f"Error saving lead: {str(e)}")
            raise
    
    def save_leads(self, leads: List[Dict[str, Any]]) -> List[int]:
        """
        Save multiple leads.
        
        Args:
            leads: List of lead dictionaries
        
        Returns:
            List of lead IDs
        """
        lead_ids = []
        for lead in leads:
            try:
                lead_id = self.save_lead(lead)
                lead_ids.append(lead_id)
            except Exception as e:
                logger.error(f"Error saving lead {lead.get('name')}: {str(e)}")
        
        return lead_ids
    
    def get_lead(self, lead_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a lead by ID.
        
        Args:
            lead_id: Lead ID
        
        Returns:
            Lead dictionary or None
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM leads WHERE id = ?", (lead_id,))
            row = cursor.fetchone()
            
            if not row:
                return None
            
            # Convert row to dictionary
            columns = [desc[0] for desc in cursor.description]
            lead = dict(zip(columns, row))
            
            # Parse JSON fields
            for field in ["score_breakdown", "recent_publication", "company_funding",
                         "conference_activity", "location_analysis", "company_research", "email_info"]:
                if lead.get(field):
                    try:
                        lead[field] = json.loads(lead[field])
                    except:
                        pass
            
            conn.close()
            return lead
        
        except Exception as e:
            logger.error(f"Error getting lead: {str(e)}")
            return None
    
    def get_all_leads(
        self,
        min_score: Optional[float] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get all leads with optional filters.
        
        Args:
            min_score: Minimum score filter
            status: Status filter
            limit: Maximum number of results
        
        Returns:
            List of leads
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            query = "SELECT * FROM leads WHERE 1=1"
            params = []
            
            if min_score is not None:
                query += " AND total_score >= ?"
                params.append(min_score)
            
            if status:
                query += " AND status = ?"
                params.append(status)
            
            query += " ORDER BY total_score DESC"
            
            if limit:
                query += " LIMIT ?"
                params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            columns = [desc[0] for desc in cursor.description]
            leads = []
            
            for row in rows:
                lead = dict(zip(columns, row))
                # Parse JSON fields
                for field in ["score_breakdown", "recent_publication", "company_funding",
                             "conference_activity", "location_analysis", "company_research", "email_info"]:
                    if lead.get(field):
                        try:
                            lead[field] = json.loads(lead[field])
                        except:
                            pass
                leads.append(lead)
            
            conn.close()
            return leads
        
        except Exception as e:
            logger.error(f"Error getting leads: {str(e)}")
            return []
    
    def update_lead_status(self, lead_id: int, status: str, notes: Optional[str] = None):
        """
        Update lead status.
        
        Args:
            lead_id: Lead ID
            status: New status
            notes: Optional notes
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE leads SET status = ?, notes = ?, last_updated = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, notes, lead_id))
            
            # Log status change
            cursor.execute("""
                INSERT INTO lead_status (lead_id, status, notes)
                VALUES (?, ?, ?)
            """, (lead_id, status, notes))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Updated lead {lead_id} status to {status}")
        
        except Exception as e:
            logger.error(f"Error updating lead status: {str(e)}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics.
        
        Returns:
            Statistics dictionary
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Total leads
            cursor.execute("SELECT COUNT(*) FROM leads")
            total_leads = cursor.fetchone()[0]
            
            # Average score
            cursor.execute("SELECT AVG(total_score) FROM leads")
            avg_score = cursor.fetchone()[0] or 0
            
            # Status counts
            cursor.execute("SELECT status, COUNT(*) FROM leads GROUP BY status")
            status_counts = dict(cursor.fetchall())
            
            # Score distribution
            cursor.execute("""
                SELECT 
                    SUM(CASE WHEN total_score >= 70 THEN 1 ELSE 0 END) as high,
                    SUM(CASE WHEN total_score >= 40 AND total_score < 70 THEN 1 ELSE 0 END) as medium,
                    SUM(CASE WHEN total_score < 40 THEN 1 ELSE 0 END) as low
                FROM leads
            """)
            score_dist = cursor.fetchone()
            
            conn.close()
            
            return {
                "total_leads": total_leads,
                "average_score": round(avg_score, 2),
                "status_counts": status_counts,
                "score_distribution": {
                    "high": score_dist[0] or 0,
                    "medium": score_dist[1] or 0,
                    "low": score_dist[2] or 0
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting statistics: {str(e)}")
            return {}


if __name__ == "__main__":
    # Test the database
    db = LeadDatabase("test_leads.db")
    
    test_lead = {
        "name": "Dr. Test User",
        "title": "Director of Toxicology",
        "company": "Test Company",
        "score": {"total_score": 85, "probability_score": 85},
        "location_analysis": {"personal_location": "Cambridge, MA"},
        "company_research": {"uses_3d_models": True}
    }
    
    lead_id = db.save_lead(test_lead)
    print(f"Saved lead with ID: {lead_id}")
    
    stats = db.get_statistics()
    print(f"Statistics: {stats}")

