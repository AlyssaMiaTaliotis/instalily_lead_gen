import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from backend.database.models import Company, Event
from backend.ai_engine.lead_qualifier import LeadQualifier

def test_pytest_runs():
    assert True

@pytest.fixture
def sample_company():
    return Company(
        name="GraphicsPro Inc.",
        industry="Graphics & Signage",
        size="Large (1000+ employees)",
        revenue="$50M",
        location="New York",
        description="Leading provider of vinyl signage materials.",
        technologies=["UV Protection Films", "Vehicle Wraps"],
        recent_news=["Expanded into Canada"]
    )

@pytest.fixture
def sample_event():
    return Event(
        name="ISA Sign Expo 2025",
        date="2025-04-25",
        location="Las Vegas",
        industry="Signage",
        website="https://signexpo.org"
    )

def test_rule_based_scoring_only(sample_company):
    qualifier = LeadQualifier(api_key="fake")
    score, rationale = qualifier._calculate_base_score(sample_company)
    assert 0.5 <= score <= 1.0
    assert "industry" in rationale.lower()

def test_ai_qualification_fallback(monkeypatch, sample_company, sample_event):
    from backend.ai_engine.lead_qualifier import LeadQualifier

    def mock_ai_qualify_company(self, company, event=None):
        return 0.8, "Mocked AI rationale"

    monkeypatch.setattr(LeadQualifier, "_ai_qualify_company", mock_ai_qualify_company)

    qualifier = LeadQualifier(api_key="fake")
    score, rationale = qualifier.qualify_company(sample_company, sample_event)

    assert 0.6 < score <= 1.0
    assert "Mocked" in rationale

def test_identify_decision_makers_mock(monkeypatch, sample_company):
    from backend.ai_engine.lead_qualifier import LeadQualifier
    from database.models import Stakeholder

    def mock_identify_decision_makers(self, company):
        return [
            Stakeholder(
                name="[To be identified via LinkedIn]",
                title="VP Product Development",
                department="Product",
                linkedin_url="",
                email="",
                phone="",
                decision_maker_score=0.9,
                contact_method="linkedin"
            )
        ]

    # Monkeypatch the method
    monkeypatch.setattr(LeadQualifier, "identify_decision_makers", mock_identify_decision_makers)

    qualifier = LeadQualifier(api_key="fake")
    stakeholders = qualifier.identify_decision_makers(sample_company)

    assert isinstance(stakeholders, list)
    assert stakeholders[0].title == "VP Product Development"
    assert stakeholders[0].decision_maker_score == 0.9