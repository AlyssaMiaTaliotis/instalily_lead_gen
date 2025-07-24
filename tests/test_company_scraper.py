import sys
import os
import pytest

# Adjust import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.scrapers.company_scraper import CompanyScraper, Company

@pytest.fixture
def company_scraper():
    return CompanyScraper()

def test_scrape_and_enrich_company(company_scraper):
    company = company_scraper.scrape_company_info("Avery Dennison Graphics Solutions")
    assert isinstance(company, Company)
    assert company.name == "Avery Dennison Graphics Solutions"
    assert company.revenue.startswith("$")
    assert "Graphics" in company.industry or "Materials" in company.industry

def test_company_qualification_score(company_scraper):
    company = Company(
        name="TestCo",
        industry="Graphics and Signage",
        size="Medium",
        revenue="$50M",
        technologies=["UV Protection", "Weather-resistant Films"],
        recent_news=["Launched outdoor product"]
    )
    score = company_scraper._calculate_qualification_score_dict(company.__dict__)
    assert 0.0 < score <= 1.0

def test_save_companies_to_csv(tmp_path, company_scraper):
    test_company = Company(
        name="Test Corp",
        website="https://test.com",
        industry="Graphics",
        size="Medium",
        revenue="$20M",
        location="Denver",
        description="Mock company for unit test",
        linkedin_url="https://linkedin.com/company/test-corp",
        technologies=["Protective Films"],
        recent_news=["Acquired new plant"],
        qualification_score=0.82
    )
    company_scraper.save_companies_to_csv([test_company], filename=tmp_path / "companies_test.csv")
    file_path = tmp_path / "companies_test.csv"
    assert file_path.exists()
    with open(file_path) as f:
        assert "Test Corp" in f.read()