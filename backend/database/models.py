from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
import sqlite3
import logging

@dataclass
class Event:
    id: Optional[int] = None
    name: str = ""
    date: str = ""
    location: str = ""
    industry: str = ""
    website: str = ""
    description: str = ""
    relevance_score: float = 0.0
    exhibitors_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Company:
    id: Optional[int] = None
    name: str = ""
    website: str = ""
    industry: str = ""
    size: str = ""
    revenue: str = ""
    location: str = ""
    description: str = ""
    linkedin_url: str = ""
    technologies: List[str] = None
    recent_news: List[str] = None
    key_contacts: List[Dict] = None
    qualification_score: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.technologies is None:
            self.technologies = []
        if self.recent_news is None:
            self.recent_news = []

@dataclass
class Stakeholder:
    id: Optional[int] = None
    company_id: Optional[int] = None
    name: str = ""
    title: str = ""
    department: str = ""
    linkedin_url: str = ""
    email: str = ""
    phone: str = ""
    decision_maker_score: float = 0.0
    contact_method: str = "linkedin"
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

@dataclass
class Lead:
    id: Optional[int] = None
    event_id: Optional[int] = None
    company_id: Optional[int] = None
    stakeholder_id: Optional[int] = None
    status: str = "new"  # new, qualified, contacted, responded, closed
    priority: str = "medium"  # high, medium, low
    overall_score: float = 0.0
    rationale: str = ""
    outreach_subject: str = ""
    outreach_message: str = ""
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    # Composite fields (populated via joins)
    event_name: Optional[str] = None
    company_name: Optional[str] = None
    stakeholder_name: Optional[str] = None

class DatabaseManager:
    def __init__(self, db_path: str = "data/leads.db"):
        self.db_path = db_path
        self.logger = self._setup_logging()
        self.init_database()

    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)

    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn

    def init_database(self):
        """Initialize database with all tables"""
        with self.get_connection() as conn:
            # Events table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    date TEXT,
                    location TEXT,
                    industry TEXT,
                    website TEXT,
                    description TEXT,
                    relevance_score REAL DEFAULT 0.0,
                    exhibitors_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Companies table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    website TEXT,
                    industry TEXT,
                    size TEXT,
                    revenue TEXT,
                    location TEXT,
                    description TEXT,
                    linkedin_url TEXT,
                    technologies TEXT, -- JSON array
                    recent_news TEXT, -- JSON array
                    qualification_score REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Stakeholders table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS stakeholders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_id INTEGER,
                    name TEXT NOT NULL,
                    title TEXT,
                    department TEXT,
                    linkedin_url TEXT,
                    email TEXT,
                    phone TEXT,
                    decision_maker_score REAL DEFAULT 0.0,
                    contact_method TEXT DEFAULT 'linkedin',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (company_id) REFERENCES companies (id)
                )
            """)
            # Leads table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS leads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER,
                    company_id INTEGER,
                    stakeholder_id INTEGER,
                    status TEXT DEFAULT 'new',
                    priority TEXT DEFAULT 'medium',
                    overall_score REAL DEFAULT 0.0,
                    rationale TEXT,
                    outreach_subject TEXT,
                    outreach_message TEXT,
                    notes TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES events (id),
                    FOREIGN KEY (company_id) REFERENCES companies (id),
                    FOREIGN KEY (stakeholder_id) REFERENCES stakeholders (id)
                )
            """)
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_companies_name ON companies(name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_companies_score ON companies(qualification_score)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_stakeholders_company ON stakeholders(company_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_priority ON leads(priority)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(overall_score)")
            conn.commit()
        self.logger.info("Database initialized successfully")

    # Event methods
    def create_event(self, event: Event) -> int:
        """Create new event and return ID"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO events (name, date, location, industry, website,
                description, relevance_score, exhibitors_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (event.name, event.date, event.location, event.industry,
                  event.website, event.description, event.relevance_score,
                  event.exhibitors_count))
            event_id = cursor.lastrowid
            conn.commit()
            return event_id

    def get_events(self, limit: int = None) -> List[Event]:
        """Get all events"""
        with self.get_connection() as conn:
            query = "SELECT * FROM events ORDER BY relevance_score DESC"
            if limit:
                query += f" LIMIT {limit}"
            rows = conn.execute(query).fetchall()
            events = []
            for row in rows:
                event = Event(
                    id=row['id'],
                    name=row['name'],
                    date=row['date'],
                    location=row['location'],
                    industry=row['industry'],
                    website=row['website'],
                    description=row['description'],
                    relevance_score=row['relevance_score'],
                    exhibitors_count=row['exhibitors_count'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                events.append(event)
            return events

    # Company methods
    def create_company(self, company: Company) -> int:
        """Create new company and return ID"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT OR REPLACE INTO companies
                (name, website, industry, size, revenue, location, description,
                 linkedin_url, technologies, recent_news, qualification_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (company.name, company.website, company.industry, company.size,
                  company.revenue, company.location, company.description,
                  company.linkedin_url, json.dumps(company.technologies),
                  json.dumps(company.recent_news), company.qualification_score))
            company_id = cursor.lastrowid
            conn.commit()
            return company_id

    def get_companies(self, limit: int = None) -> List[Company]:
        """Get all companies"""
        with self.get_connection() as conn:
            query = "SELECT * FROM companies ORDER BY qualification_score DESC"
            if limit:
                query += f" LIMIT {limit}"
            rows = conn.execute(query).fetchall()
            companies = []
            for row in rows:
                company = Company(
                    id=row['id'],
                    name=row['name'],
                    website=row['website'],
                    industry=row['industry'],
                    size=row['size'],
                    revenue=row['revenue'],
                    location=row['location'],
                    description=row['description'],
                    linkedin_url=row['linkedin_url'],
                    technologies=json.loads(row['technologies'] or '[]'),
                    recent_news=json.loads(row['recent_news'] or '[]'),
                    qualification_score=row['qualification_score'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                companies.append(company)
            return companies

    def get_company_by_name(self, name: str) -> Optional[Company]:
        """Get company by name"""
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM companies WHERE name = ?", (name,)).fetchone()
            if row:
                return Company(
                    id=row['id'],
                    name=row['name'],
                    website=row['website'],
                    industry=row['industry'],
                    size=row['size'],
                    revenue=row['revenue'],
                    location=row['location'],
                    description=row['description'],
                    linkedin_url=row['linkedin_url'],
                    technologies=json.loads(row['technologies'] or '[]'),
                    recent_news=json.loads(row['recent_news'] or '[]'),
                    qualification_score=row['qualification_score'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            return None

    # Stakeholder methods
    def create_stakeholder(self, stakeholder: Stakeholder) -> int:
        """Create new stakeholder and return ID"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO stakeholders
                (company_id, name, title, department, linkedin_url, email, phone,
                 decision_maker_score, contact_method)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (stakeholder.company_id, stakeholder.name, stakeholder.title,
                  stakeholder.department, stakeholder.linkedin_url, stakeholder.email,
                  stakeholder.phone, stakeholder.decision_maker_score,
                  stakeholder.contact_method))
            stakeholder_id = cursor.lastrowid
            conn.commit()
            return stakeholder_id

    def get_stakeholders_by_company(self, company_id: int) -> List[Stakeholder]:
        """Get all stakeholders for a company"""
        with self.get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM stakeholders
                WHERE company_id = ?
                ORDER BY decision_maker_score DESC
            """, (company_id,)).fetchall()
            stakeholders = []
            for row in rows:
                stakeholder = Stakeholder(
                    id=row['id'],
                    company_id=row['company_id'],
                    name=row['name'],
                    title=row['title'],
                    department=row['department'],
                    linkedin_url=row['linkedin_url'],
                    email=row['email'],
                    phone=row['phone'],
                    decision_maker_score=row['decision_maker_score'],
                    contact_method=row['contact_method'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                stakeholders.append(stakeholder)
            return stakeholders

    # Lead methods
    def create_lead(self, lead: Lead) -> int:
        """Create new lead and return ID"""
        with self.get_connection() as conn:
            cursor = conn.execute("""
                INSERT INTO leads
                (event_id, company_id, stakeholder_id, status, priority, overall_score,
                 rationale, outreach_subject, outreach_message, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (lead.event_id, lead.company_id, lead.stakeholder_id, lead.status,
                  lead.priority, lead.overall_score, lead.rationale,
                  lead.outreach_subject, lead.outreach_message, lead.notes))
            lead_id = cursor.lastrowid
            conn.commit()
            return lead_id

    def get_leads(self, status: str = None, limit: int = None) -> List[Lead]:
        """Get leads with optional filtering"""
        with self.get_connection() as conn:
            query = """
                SELECT l.*, e.name as event_name, c.name as company_name, s.name as stakeholder_name
                FROM leads l
                LEFT JOIN events e ON l.event_id = e.id
                LEFT JOIN companies c ON l.company_id = c.id
                LEFT JOIN stakeholders s ON l.stakeholder_id = s.id
            """
            params = []
            if status:
                query += " WHERE l.status = ?"
                params.append(status)
            query += " ORDER BY l.overall_score DESC"
            if limit:
                query += f" LIMIT {limit}"
            rows = conn.execute(query, params).fetchall()
            leads = []
            for row in rows:
                lead = Lead(
                    id=row['id'],
                    event_id=row['event_id'],
                    company_id=row['company_id'],
                    stakeholder_id=row['stakeholder_id'],
                    status=row['status'],
                    priority=row['priority'],
                    overall_score=row['overall_score'],
                    rationale=row['rationale'],
                    outreach_subject=row['outreach_subject'],
                    outreach_message=row['outreach_message'],
                    notes=row['notes'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at'],
                    event_name=row['event_name'],
                    company_name=row['company_name'],
                    stakeholder_name=row['stakeholder_name']
                )
                leads.append(lead)
            return leads

    def update_lead_status(self, lead_id: int, status: str, notes: str = None):
        """Update lead status"""
        with self.get_connection() as conn:
            if notes:
                conn.execute("""
                    UPDATE leads
                    SET status = ?, notes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, notes, lead_id))
            else:
                conn.execute("""
                    UPDATE leads
                    SET status = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (status, lead_id))
            conn.commit()

    def get_lead_stats(self) -> Dict[str, Any]:
        """Get lead statistics for dashboard"""
        with self.get_connection() as conn:
            stats = {}
            # Total counts
            stats['total_leads'] = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
            stats['total_companies'] = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
            stats['total_events'] = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
            # Status breakdown
            status_rows = conn.execute("""
                SELECT status, COUNT(*) as count
                FROM leads
                GROUP BY status
            """).fetchall()
            stats['status_breakdown'] = {row[0]: row[1] for row in status_rows}
            # Priority breakdown
            priority_rows = conn.execute("""
                SELECT priority, COUNT(*) as count
                FROM leads
                GROUP BY priority
            """).fetchall()
            stats['priority_breakdown'] = {row[0]: row[1] for row in priority_rows}
            # Top companies by score
            top_companies = conn.execute("""
                SELECT name, qualification_score
                FROM companies
                ORDER BY qualification_score DESC
                LIMIT 5
            """).fetchall()
            stats['top_companies'] = [
                {'name': row[0], 'score': row[1]} for row in top_companies
            ]
            return stats

    def export_leads_to_dict(self) -> List[Dict[str, Any]]:
        """Export all leads to dictionary format for API/CSV"""
        leads = self.get_leads()
        return [asdict(lead) for lead in leads]

# Utility functions
def populate_sample_data(db: DatabaseManager):
    """Populate database with sample data for testing"""
    # Sample events
    events = [
        Event(name="ISA Sign Expo 2025", date="April 24-26, 2025",
              location="Las Vegas, NV", industry="Signage & Graphics",
              website="https://signexpo.org", relevance_score=0.95),
        Event(name="PRINTING United Expo 2025", date="October 19-21, 2025",
              location="Atlanta, GA", industry="Printing & Graphics",
              website="https://printingunited.com", relevance_score=0.85)
    ]
    for event in events:
        db.create_event(event)
    # Sample companies
    companies = [
        Company(name="Avery Dennison Graphics Solutions",
                industry="Specialty Materials & Graphics",
                size="Large (35,000+ employees)", revenue="$8.2B",
                qualification_score=0.92),
        Company(name="3M Commercial Solutions",
                industry="Industrial Materials & Graphics",
                size="Large (95,000+ employees)", revenue="$35B",
                qualification_score=0.88)
    ]
    for company in companies:
        db.create_company(company)

if __name__ == "__main__":
    # Test database setup
    db = DatabaseManager()
    populate_sample_data(db)
    stats = db.get_lead_stats()
    print("Database Stats:", stats)