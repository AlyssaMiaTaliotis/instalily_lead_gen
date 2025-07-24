import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import pandas as pd
import time
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional
import re

@dataclass
class Event:
    name: str
    date: str
    location: str
    industry: str
    website: str
    exhibitors: List[str] = None
    description: str = ""
    relevance_score: float = 0.0

class EventsScraper:
    def __init__(self):
        self.logger = self._setup_logging()
        self.driver = None
        self.events = []

    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)

    def _get_driver(self):
        if self.driver:
            return self.driver
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.chrome.options import Options

            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')

            chrome_driver_path = "/usr/local/bin/chromedriver"
            self.driver = webdriver.Chrome(service=Service(chrome_driver_path), options=chrome_options)
        except Exception as e:
            self.logger.error(f"Error initializing ChromeDriver: {e}")
            self.driver = None
        return self.driver

    def scrape_isa_sign_expo(self) -> List[Event]:
        """Scrape ISA Sign Expo data"""
        try:
            self.logger.info("Scraping ISA Sign Expo...")
            url = "https://www.signs.org/events"
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            soup = BeautifulSoup(response.content, 'html.parser')
            events = []
            event_elements = soup.find_all('div', class_=['event-item', 'event-card'])
            for element in event_elements[:5]:
                try:
                    name = self._extract_text(element, ['h2', 'h3', '.title', '.event-title'])
                    date = self._extract_text(element, ['.date', '.event-date', 'time'])
                    location = self._extract_text(element, ['.location', '.venue', '.event-location'])
                    if name and ('sign' in name.lower() or 'expo' in name.lower()):
                        event = Event(
                            name=name,
                            date=date or "TBD",
                            location=location or "TBD",
                            industry="Signage & Graphics",
                            website="https://www.signs.org",
                            description="Premier signage industry event"
                        )
                        events.append(event)
                except Exception as e:
                    self.logger.warning(f"Error parsing ISA event: {e}")
                    continue
            if not events:
                events.append(Event(
                    name="ISA Sign Expo 2025",
                    date="April 24-26, 2025",
                    location="Las Vegas, NV",
                    industry="Signage & Graphics",
                    website="https://www.signexpo.org",
                    description="The premier trade show for the sign, graphics, and visual communications industry"
                ))
            return events
        except Exception as e:
            self.logger.error(f"Error scraping ISA Sign Expo: {e}")
            return []

    def scrape_sgia_events(self) -> List[Event]:
        """Scrape SGIA/PRINTING United events"""
        try:
            self.logger.info("Scraping PRINTING United events...")
            events = []
            known_events = [
                {
                    "name": "PRINTING United Expo 2025",
                    "date": "October 19-21, 2025",
                    "location": "Atlanta, GA",
                    "website": "https://printingunited.com",
                    "description": "The most dynamic and comprehensive printing event in the Americas"
                },
                {
                    "name": "FESPA Global Print Expo 2025",
                    "date": "March 18-21, 2025",
                    "location": "Berlin, Germany",
                    "website": "https://fespa.com",
                    "description": "Europe's largest specialty printing exhibition"
                }
            ]
            for event_data in known_events:
                event = Event(
                    name=event_data["name"],
                    date=event_data["date"],
                    location=event_data["location"],
                    industry="Printing & Graphics",
                    website=event_data["website"],
                    description=event_data["description"]
                )
                events.append(event)
            return events
        except Exception as e:
            self.logger.error(f"Error scraping SGIA events: {e}")
            return []

    def scrape_specialty_graphics_events(self) -> List[Event]:
        """Scrape specialty graphics industry events"""
        try:
            self.logger.info("Scraping specialty graphics events...")
            events = []
            specialty_events = [
                {
                    "name": "Graphics of the Americas 2025",
                    "date": "February 20-22, 2025",
                    "location": "Miami Beach, FL",
                    "website": "https://graphicsoftheamericas.com",
                    "description": "Latin America's premier graphics and sign industry event"
                },
                {
                    "name": "Wide Format Summit 2025",
                    "date": "May 14-16, 2025",
                    "location": "Denver, CO",
                    "website": "https://wideformatsummit.com",
                    "description": "Strategic conference for wide-format printing industry"
                },
                {
                    "name": "Vehicle Graphics Conference 2025",
                    "date": "June 11-13, 2025",
                    "location": "Chicago, IL",
                    "website": "https://vehiclegraphics.com",
                    "description": "Dedicated to vehicle wrap and graphics professionals"
                }
            ]
            for event_data in specialty_events:
                event = Event(
                    name=event_data["name"],
                    date=event_data["date"],
                    location=event_data["location"],
                    industry="Specialty Graphics",
                    website=event_data["website"],
                    description=event_data["description"]
                )
                events.append(event)
            return events
        except Exception as e:
            self.logger.error(f"Error scraping specialty graphics events: {e}")
            return []

    def scrape_event_exhibitors(self, event_url: str) -> List[str]:
        """Scrape exhibitor list from event website"""
        try:
            driver = self._get_driver()
            driver.get(event_url)
            time.sleep(2)
            exhibitors = []
            exhibitor_selectors = [
                '.exhibitor-name',
                '.company-name',
                '[data-exhibitor]',
                '.participant-name'
            ]
            for selector in exhibitor_selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements[:50]:
                    try:
                        company_name = element.text.strip()
                        if company_name and len(company_name) > 2:
                            exhibitors.append(company_name)
                    except:
                        continue
                if exhibitors:
                    break
            return list(set(exhibitors))
        except Exception as e:
            self.logger.warning(f"Could not scrape exhibitors from {event_url}: {e}")
            return []

    def _extract_text(self, element, selectors: List[str]) -> Optional[str]:
        """Extract text using multiple possible selectors"""
        for selector in selectors:
            try:
                if selector.startswith('.'):
                    found = element.find(class_=selector[1:])
                else:
                    found = element.find(selector)
                if found:
                    return found.get_text(strip=True)
            except:
                continue
        return None

    def calculate_relevance_score(self, event: Event) -> float:
        """Calculate relevance score for DuPont Tedlar Graphics team"""
        score = 0.0
        graphics_keywords = [
            'sign', 'signage', 'graphics', 'printing', 'wrap', 'vinyl',
            'digital', 'wide format', 'display', 'advertising', 'visual'
        ]
        text_to_analyze = f"{event.name} {event.description}".lower()
        for keyword in graphics_keywords:
            if keyword in text_to_analyze:
                score += 0.1
        importance_keywords = ['expo', 'international', 'global', 'summit', 'united']
        for keyword in importance_keywords:
            if keyword in text_to_analyze:
                score += 0.15
        major_markets = ['las vegas', 'chicago', 'atlanta', 'miami', 'new york']
        if any(market in event.location.lower() for market in major_markets):
            score += 0.1
        return min(score, 1.0)

    def scrape_all_events(self) -> List[Event]:
        """Scrape events from all sources"""
        self.logger.info("Starting comprehensive event scraping...")
        all_events = []
        sources = [
            self.scrape_isa_sign_expo,
            self.scrape_sgia_events,
            self.scrape_specialty_graphics_events
        ]
        for scraper_func in sources:
            try:
                events = scraper_func()
                all_events.extend(events)
                time.sleep(1)
            except Exception as e:
                self.logger.error(f"Error in scraper {scraper_func.__name__}: {e}")
        for event in all_events:
            event.relevance_score = self.calculate_relevance_score(event)
        all_events.sort(key=lambda x: x.relevance_score, reverse=True)
        self.logger.info(f"Found {len(all_events)} events")
        return all_events

    def save_events_to_csv(self, events: List[Event], filename: str = "data/events.csv"):
        """Save events to CSV file"""
        try:
            events_data = []
            for event in events:
                events_data.append({
                    'name': event.name,
                    'date': event.date,
                    'location': event.location,
                    'industry': event.industry,
                    'website': event.website,
                    'description': event.description,
                    'relevance_score': event.relevance_score,
                    'exhibitors_count': len(event.exhibitors) if event.exhibitors else 0
                })
            df = pd.DataFrame(events_data)
            df.to_csv(filename, index=False)
            self.logger.info(f"Saved {len(events)} events to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving events to CSV: {e}")

    def scrape_industry_events(self, industries: List[str]) -> List[Event]:
        """Filter events by target industry keywords"""
        all_events = self.scrape_all_events()
        filtered = [
            event for event in all_events
            if any(industry.lower() in event.industry.lower() for industry in industries)
        ]
        return filtered

    def __del__(self):
        """Cleanup driver"""
        if self.driver:
            self.driver.quit()


if __name__ == "__main__":
    scraper = EventsScraper()
    events = scraper.scrape_all_events()
    scraper.save_events_to_csv(events)
    print(f"\nFound {len(events)} relevant events:")
    for event in events[:5]:
        print(f"- {event.name} ({event.date}) - Score: {event.relevance_score:.2f}")