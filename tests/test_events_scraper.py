import sys
import os
import pytest

# Ensure correct import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.scrapers.events_scraper import EventsScraper, Event


@pytest.fixture
def scraper():
    return EventsScraper()

def test_scrape_known_fallback_events(scraper):
    # SGIA and Specialty graphics fallback events should always return at least 2 each
    sgia_events = scraper.scrape_sgia_events()
    specialty_events = scraper.scrape_specialty_graphics_events()

    assert len(sgia_events) >= 2
    assert len(specialty_events) >= 2
    assert isinstance(sgia_events[0], Event)
    assert isinstance(specialty_events[0], Event)

def test_relevance_score_calculation(scraper):
    event = Event(
        name="Global Sign & Graphics Expo",
        date="2025-10-10",
        location="Las Vegas, NV",
        industry="Signage",
        website="https://example.com",
        description="Focused on durable, weather-resistant graphics materials"
    )
    score = scraper.calculate_relevance_score(event)
    assert 0.0 <= score <= 1.0
    assert score > 0.5 # Should have decent score due to keywords + location

def test_event_csv_save(tmp_path, scraper):
    test_event = Event(
        name="Test Expo",
        date="2025-01-01",
        location="Chicago",
        industry="Graphics",
        website="https://test.com",
        description="A mock test event",
        relevance_score=0.75
    )
    scraper.save_events_to_csv([test_event], filename=tmp_path / "events_test.csv")

    file_path = tmp_path / "events_test.csv"
    assert file_path.exists()
    with open(file_path) as f:
        content = f.read()
        assert "Test Expo" in content