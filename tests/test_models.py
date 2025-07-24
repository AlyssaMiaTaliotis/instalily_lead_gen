import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from backend.database.models import DatabaseManager, Company, Event, Stakeholder, Lead

def test_pytest_collection_works():
    assert True

@pytest.fixture
def db():
    """Initialize a temporary test database"""
    test_db_path = "test_leads.db"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    db = DatabaseManager(test_db_path)
    yield db
    os.remove(test_db_path)

def test_create_and_get_event(db):
    event = Event(
        name="Test Expo",
        date="2025-08-15",
        location="Miami, FL",
        industry="Signage",
        website="https://testexpo.com",
        relevance_score=0.85
    )
    event_id = db.create_event(event)
    assert event_id > 0
    events = db.get_events()
    assert len(events) == 1
    assert events[0].name == "Test Expo"

def test_create_company_and_fetch(db):
    company = Company(
        name="SignCo Test",
        industry="Graphics",
        size="Medium",
        revenue="$25M",
        technologies=["Adhesive Films"],
        recent_news=["Launched new outdoor wrap"]
    )
    company_id = db.create_company(company)
    assert company_id > 0
    companies = db.get_companies()
    assert companies[0].name == "SignCo Test"

def test_create_stakeholder(db):
    company = Company(name="StakeCo")
    company_id = db.create_company(company)

    stakeholder = Stakeholder(
        company_id=company_id,
        name="Jane Doe",
        title="VP Product",
        department="Product"
    )
    stakeholder_id = db.create_stakeholder(stakeholder)
    assert stakeholder_id > 0

    stakeholders = db.get_stakeholders_by_company(company_id)
    assert stakeholders[0].name == "Jane Doe"

def test_create_lead(db):
    event_id = db.create_event(Event(name="Lead Expo"))
    company_id = db.create_company(Company(name="LeadCorp"))
    stakeholder_id = db.create_stakeholder(Stakeholder(company_id=company_id, name="VP Ops"))

    lead = Lead(
        event_id=event_id,
        company_id=company_id,
        stakeholder_id=stakeholder_id,
        status="qualified",
        priority="high",
        rationale="Test lead",
        outreach_subject="Hi",
        outreach_message="Hello!"
    )

    lead_id = db.create_lead(lead)
    assert lead_id > 0
    leads = db.get_leads()
    assert leads[0].status == "qualified"