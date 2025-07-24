import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import logging
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import json

@dataclass
class Company:
    name: str
    website: str = ""
    industry: str = ""
    size: str = ""
    revenue: str = ""
    location: str = ""
    description: str = ""
    linkedin_url: str = ""
    technologies: List[str] = None
    recent_news: List[str] = None
    qualification_score: float = 0.0
    key_contacts: List[Dict] = None

    def __post_init__(self):
        if self.technologies is None:
            self.technologies = []
        if self.recent_news is None:
            self.recent_news = []
        if self.key_contacts is None:
            self.key_contacts = []

class CompanyScraper:
    def __init__(self):
        self.logger = self._setup_logging()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        # Target companies in graphics/signage industry
        self.target_companies = [
            "Avery Dennison Graphics Solutions",
            "3M Commercial Solutions",
            "Orafol Americas",
            "FLEXcon Company",
            "Mactac Americas",
            "General Formulations",
            "Drytac Corporation",
            "Arlon Graphics",
            "Metamark UK",
            "Hexis Graphics",
            "Roland DGA Corporation",
            "HP Large Format Printing",
            "Mimaki USA",
            "Mutoh America",
            "Canon Solutions America",
            "Epson Professional Imaging",
            "Signs.com",
            "FastSigns International",
            "YESCO",
            "Image360",
            "SpeedPro Imaging"
        ]

    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)

    def extract_companies_from_event(self, event) -> List[Dict]:
        """Extract companies from event data - NEW METHOD"""
        try:
            self.logger.info(f"Extracting companies from event: {event.name}")
            companies = []
            # If event has exhibitors list, use that
            if hasattr(event, 'exhibitors') and event.exhibitors:
                for exhibitor_name in event.exhibitors:
                    company_data = {
                        'name': exhibitor_name,
                        'source_event': event.name,
                        'industry': event.industry,
                        'event_date': event.date,
                        'event_location': event.location
                    }
                    companies.append(company_data)
            # Otherwise, try to scrape from event website
            elif hasattr(event, 'website') and event.website:
                try:
                    scraped_companies = self._scrape_exhibitors_from_website(event.website)
                    for company_name in scraped_companies:
                        company_data = {
                            'name': company_name,
                            'source_event': event.name,
                            'industry': event.industry,
                            'event_date': event.date,
                            'event_location': event.location
                        }
                        companies.append(company_data)
                except Exception as e:
                    self.logger.warning(f"Could not scrape exhibitors from {event.website}: {e}")
            # If no companies found from event, use our target companies list
            if not companies:
                self.logger.info(f"No exhibitors found for {event.name}, using target companies")
                for company_name in self.target_companies[:10]: # Limit to 10 for this event
                    company_data = {
                        'name': company_name,
                        'source_event': event.name,
                        'industry': event.industry,
                        'event_date': event.date,
                        'event_location': event.location,
                        'is_target_company': True
                    }
                    companies.append(company_data)
            self.logger.info(f"Extracted {len(companies)} companies from {event.name}")
            return companies
        except Exception as e:
            self.logger.error(f"Error extracting companies from event {event.name}: {e}")
            return []

    def _scrape_exhibitors_from_website(self, event_url: str) -> List[str]:
        """Scrape exhibitor names from event website"""
        try:
            response = self.session.get(event_url, timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            exhibitors = []
            # Common patterns for exhibitor listings
            exhibitor_selectors = [
                '.exhibitor-name',
                '.company-name',
                '[data-exhibitor]',
                '.participant-name',
                '.sponsor-name',
                '.vendor-name'
            ]
            for selector in exhibitor_selectors:
                try:
                    elements = soup.select(selector)
                    for element in elements[:50]: # Limit to avoid overwhelming
                        company_name = element.get_text(strip=True)
                        if company_name and len(company_name) > 2:
                            exhibitors.append(company_name)
                    if exhibitors:
                        break # Found exhibitors with this selector
                except:
                    continue
            # If no specific selectors work, try to find company names in text
            if not exhibitors:
                page_text = soup.get_text()
                # Look for common company suffixes
                company_patterns = [
                    r'([A-Z][a-zA-Z\s&]+(?:Inc|LLC|Corp|Corporation|Company|Solutions|Systems|Technologies)\.?)',
                    r'([A-Z][a-zA-Z\s&]+(?:Group|Industries|International|Global)\.?)'
                ]
                for pattern in company_patterns:
                    matches = re.findall(pattern, page_text)
                    exhibitors.extend(matches[:20]) # Limit results
                    if exhibitors:
                        break
            return list(set(exhibitors)) # Remove duplicates
        except Exception as e:
            self.logger.warning(f"Could not scrape exhibitors from {event_url}: {e}")
            return []

    def enrich_company_data(self, company_dict: Dict) -> Dict:
        """Enrich company data dictionary - UPDATED METHOD"""
        try:
            self.logger.info(f"Enriching data for {company_dict.get('name', 'Unknown')}")
            # Create a copy to avoid modifying original
            enriched = company_dict.copy()
            company_name = company_dict.get('name', '')
            # Get website if not already present
            if not enriched.get('website'):
                enriched['website'] = self.search_company_website(company_name)
            # Scrape company website for additional info
            if enriched.get('website'):
                website_data = self._scrape_website_data(enriched['website'])
                enriched.update(website_data)
            # Add intelligence data from our knowledge base
            intelligence = self._get_company_intelligence(company_name)
            enriched.update(intelligence)
            # Add key contacts (simulated data)
            enriched['key_contacts'] = self._get_key_contacts(company_name)
            # Calculate qualification score
            enriched['qualification_score'] = self._calculate_qualification_score_dict(enriched)
            return enriched
        except Exception as e:
            self.logger.error(f"Error enriching company data for {company_dict.get('name')}: {e}")
            return company_dict

    def _scrape_website_data(self, website_url: str) -> Dict:
        """Scrape additional data from company website"""
        try:
            response = self.session.get(website_url, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            data = {}
            # Extract description
            description_sources = [
                soup.find('meta', {'name': 'description'}),
                soup.find('meta', {'property': 'og:description'}),
                soup.find('div', class_=['about', 'company-description', 'overview']),
                soup.find('section', class_=['about', 'company-info'])
            ]
            for source in description_sources:
                if source:
                    if source.name == 'meta':
                        data['description'] = source.get('content', '')[:500]
                    else:
                        data['description'] = source.get_text(strip=True)[:500]
                    break
            # Look for technology keywords
            page_text = soup.get_text().lower()
            graphics_tech_keywords = [
                'vinyl graphics', 'vehicle wraps', 'digital printing', 'wide format',
                'signage solutions', 'adhesive films', 'protective films',
                'architectural films', 'decorative films', 'window films',
                'floor graphics', 'wall graphics', 'outdoor signage'
            ]
            found_technologies = []
            for keyword in graphics_tech_keywords:
                if keyword in page_text:
                    found_technologies.append(keyword.title())
            data['technologies'] = found_technologies[:5]
            # Extract contact information
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
            emails = re.findall(email_pattern, soup.get_text())
            phones = re.findall(phone_pattern, soup.get_text())
            if emails:
                data['contact_email'] = emails[0]
            if phones:
                data['contact_phone'] = phones[0]
            return data
        except Exception as e:
            self.logger.warning(f"Error scraping website data from {website_url}: {e}")
            return {}

    def _get_company_intelligence(self, company_name: str) -> Dict:
        """Get intelligence data for company"""
        # Enhanced company intelligence database
        company_intelligence = {
            "Avery Dennison Graphics Solutions": {
                "revenue": "$8.2B",
                "size": "Large (35,000+ employees)",
                "industry": "Specialty Materials & Graphics",
                "location": "Glendale, CA",
                "linkedin_url": "https://linkedin.com/company/avery-dennison",
                "recent_news": [
                    "Launched new sustainable graphic films line",
                    "Expanded manufacturing capacity in Asia-Pacific"
                ]
            },
            "3M Commercial Solutions": {
                "revenue": "$35B (total 3M)",
                "size": "Large (95,000+ employees)",
                "industry": "Industrial Materials & Graphics",
                "location": "St. Paul, MN",
                "linkedin_url": "https://linkedin.com/company/3m",
                "recent_news": [
                    "Introduced new architectural window films",
                    "Investing in digital printing technologies"
                ]
            },
            "Roland DGA Corporation": {
                "revenue": "$500M",
                "size": "Medium (1,500+ employees)",
                "industry": "Digital Printing Equipment",
                "location": "Irvine, CA",
                "linkedin_url": "https://linkedin.com/company/roland-dga",
                "recent_news": [
                    "Launched new wide-format UV printer series",
                    "Partnership with software solutions provider"
                ]
            },
            "HP Large Format Printing": {
                "revenue": "$63B (total HP)",
                "size": "Large (51,000+ employees)",
                "industry": "Digital Printing Solutions",
                "location": "Palo Alto, CA",
                "linkedin_url": "https://linkedin.com/company/hp",
                "recent_news": [
                    "New latex printing technology launch",
                    "Sustainability initiatives in printing"
                ]
            },
            "FastSigns International": {
                "revenue": "$600M",
                "size": "Medium (2,000+ employees)",
                "industry": "Sign & Graphics Franchise",
                "location": "Carrollton, TX",
                "linkedin_url": "https://linkedin.com/company/fastsigns",
                "recent_news": [
                    "Expanded franchise network internationally",
                    "New digital signage solutions launched"
                ]
            }
        }
        if company_name in company_intelligence:
            return company_intelligence[company_name]
        else:
            # Provide estimated data based on company name/type
            estimated_data = {
                "revenue": "$50M+",
                "size": "Medium (100-500 employees)",
                "industry": "Graphics & Signage",
                "location": "United States",
                "linkedin_url": "",
                "recent_news": []
            }
            # Adjust estimates based on keywords
            name_lower = company_name.lower()
            if any(word in name_lower for word in ['international', 'global', 'solutions']):
                estimated_data["size"] = "Large (1000+ employees)"
                estimated_data["revenue"] = "$100M+"
            elif any(word in name_lower for word in ['corporation', 'systems', 'technologies']):
                estimated_data["size"] = "Medium (100-1000 employees)"
                estimated_data["revenue"] = "$50M+"
            else:
                estimated_data["size"] = "Small-Medium (50-500 employees)"
                estimated_data["revenue"] = "$10M+"
            return estimated_data

    def _get_key_contacts(self, company_name: str) -> List[Dict]:
        """Get key contacts for company (simulated data)"""
        # In production, this would integrate with LinkedIn Sales Navigator, ZoomInfo, etc.
        contact_templates = [
            {"title": "VP of Sales", "department": "Sales"},
            {"title": "Marketing Director", "department": "Marketing"},
            {"title": "Business Development Manager", "department": "Business Development"},
            {"title": "Product Manager", "department": "Product"},
            {"title": "Operations Director", "department": "Operations"}
        ]
        contacts = []
        for i, template in enumerate(contact_templates[:2]):  # Limit to 2 contacts
            contact = {
                "name": f"Contact {i+1}",  # In production, use real names
                "title": template["title"],
                "department": template["department"],
                "linkedin": f"https://linkedin.com/in/contact{i+1}",
                "email": f"contact{i+1}@{company_name.lower().replace(' ', '').replace('.', '')}.com"
            }
            contacts.append(contact)
        return contacts

    def _calculate_qualification_score_dict(self, company_data: Dict) -> float:
        """Calculate qualification score for company dictionary"""
        score = 0.0
        # Industry fit scoring
        industry = company_data.get('industry', '')
        if industry:
            graphics_industries = [
                'graphics', 'signage', 'printing', 'specialty materials',
                'adhesive', 'films', 'digital', 'visual communications'
            ]
            industry_lower = industry.lower()
            for keyword in graphics_industries:
                if keyword in industry_lower:
                    score += 0.15
        # Company size scoring
        size = company_data.get('size', '')
        if size:
            size_lower = size.lower()
            if 'large' in size_lower:
                score += 0.3
            elif 'medium' in size_lower:
                score += 0.2
            elif 'small' in size_lower:
                score += 0.1
        # Revenue scoring
        revenue = company_data.get('revenue', '')
        if revenue:
            revenue_text = revenue.lower()
            if 'b' in revenue_text or 'billion' in revenue_text:
                score += 0.25
            elif 'm' in revenue_text or 'million' in revenue_text:
                score += 0.15
        # Technology alignment scoring
        technologies = company_data.get('technologies', [])
        if technologies:
            relevant_tech_count = len([tech for tech in technologies
                                       if any(word in tech.lower()
                                              for word in ['film', 'graphic', 'wrap', 'adhesive'])])
            score += min(relevant_tech_count * 0.1, 0.2)
        # Recent market activity
        recent_news = company_data.get('recent_news', [])
        if recent_news:
            innovation_keywords = ['launch', 'new', 'innovative', 'expand', 'partnership']
            for news in recent_news:
                if any(keyword in str(news).lower() for keyword in innovation_keywords):
                    score += 0.05
        # Website and digital presence
        if company_data.get('website'):
            score += 0.05
        if company_data.get('linkedin_url'):
            score += 0.05
        # Event participation bonus
        if company_data.get('source_event'):
            score += 0.1
        return min(score, 1.0)  # Cap at 1.0

    # Keep existing methods for backward compatibility
    def search_company_website(self, company_name: str) -> Optional[str]:
        """Find company website using search"""
        try:
            # Try common website patterns first
            domain_patterns = [
                company_name.lower().replace(' ', '').replace('.', '') + '.com',
                company_name.lower().replace(' ', '-') + '.com',
                company_name.split()[0].lower() + '.com'
            ]
            for domain in domain_patterns:
                try:
                    response = self.session.get(f'https://{domain}', timeout=10)
                    if response.status_code == 200:
                        return f'https://{domain}'
                except:
                    continue
            # Fallback to constructed URL
            return f"https://www.{company_name.lower().replace(' ', '')}.com"
        except Exception as e:
            self.logger.warning(f"Could not find website for {company_name}: {e}")
            return None

    def scrape_company_info(self, company_name: str) -> Company:
        """Scrape comprehensive company information"""
        self.logger.info(f"Scraping info for {company_name}")
        company = Company(name=company_name)
        # Get website
        company.website = self.search_company_website(company_name)
        if company.website:
            # Scrape company website
            company = self._scrape_company_website(company)
            # Enrich with additional data sources
            company = self._enrich_company_data(company)
            # Calculate qualification score
            company.qualification_score = self.calculate_relevance_score(company)
        return company

    def _scrape_company_website(self, company: Company) -> Company:
        """Scrape information from company website"""
        try:
            response = self.session.get(company.website, timeout=15)
            soup = BeautifulSoup(response.content, 'html.parser')
            # Extract description from meta tags or about sections
            description_sources = [
                soup.find('meta', {'name': 'description'}),
                soup.find('meta', {'property': 'og:description'}),
                soup.find('div', class_=['about', 'company-description', 'overview']),
                soup.find('section', class_=['about', 'company-info'])
            ]
            for source in description_sources:
                if source:
                    if source.name == 'meta':
                        company.description = source.get('content', '')[:500]
                    else:
                        company.description = source.get_text(strip=True)[:500]
                    break
            # Look for industry/technology keywords
            page_text = soup.get_text().lower()
            graphics_tech_keywords = [
                'vinyl graphics', 'vehicle wraps', 'digital printing', 'wide format',
                'signage solutions', 'adhesive films', 'protective films',
                'architectural films', 'decorative films', 'window films',
                'floor graphics', 'wall graphics', 'outdoor signage'
            ]
            found_technologies = []
            for keyword in graphics_tech_keywords:
                if keyword in page_text:
                    found_technologies.append(keyword.title())
            company.technologies = found_technologies[:5]  # Limit to top 5
            # Try to determine company size indicators
            size_indicators = {
                'global': 'Large (1000+ employees)',
                'worldwide': 'Large (1000+ employees)',
                'international': 'Medium (100-1000 employees)',
                'nationwide': 'Medium (100-1000 employees)',
                'regional': 'Small (10-100 employees)'
            }
            for indicator, size in size_indicators.items():
                if indicator in page_text:
                    company.size = size
                    break
        except Exception as e:
            self.logger.warning(f"Error scraping website for {company.name}: {e}")
        return company

    def _enrich_company_data(self, company: Company) -> Company:
        """Enrich company data with additional sources"""
        intelligence = self._get_company_intelligence(company.name)
        company.revenue = intelligence.get("revenue", "")
        company.size = intelligence.get("size", company.size)
        company.industry = intelligence.get("industry", "")
        company.location = intelligence.get("location", "")
        company.linkedin_url = intelligence.get("linkedin_url", "")
        company.recent_news = intelligence.get("recent_news", [])
        return company

    def calculate_relevance_score(self, company: Company) -> float:
        """Calculate relevance score for DuPont Tedlar"""
        score = 0.0
        # Industry fit scoring
        if company.industry:
            graphics_industries = [
                'graphics', 'signage', 'printing', 'specialty materials',
                'adhesive', 'films', 'digital', 'visual communications'
            ]
            industry_lower = company.industry.lower()
            for keyword in graphics_industries:
                if keyword in industry_lower:
                    score += 0.15
        # Company size scoring
        size_scores = {
            'large': 0.3,
            'medium': 0.2,
            'small': 0.1
        }
        if company.size:
            size_lower = company.size.lower()
            for size_type, points in size_scores.items():
                if size_type in size_lower:
                    score += points
                    break
        # Revenue scoring
        if company.revenue:
            revenue_text = company.revenue.lower()
            if '$' in revenue_text:
                if 'b' in revenue_text or 'billion' in revenue_text:
                    score += 0.25
                elif 'm' in revenue_text or 'million' in revenue_text:
                    score += 0.15
        # Technology alignment scoring
        if company.technologies:
            relevant_tech_count = len([tech for tech in company.technologies
                                       if any(word in tech.lower()
                                              for word in ['film', 'graphic', 'wrap', 'adhesive'])])
            score += min(relevant_tech_count * 0.1, 0.2)
        # Recent market activity
        if company.recent_news:
            innovation_keywords = ['launch', 'new', 'innovative', 'expand', 'partnership']
            for news in company.recent_news:
                if any(keyword in news.lower() for keyword in innovation_keywords):
                    score += 0.05
        # Website and digital presence
        if company.website:
            score += 0.05
        if company.linkedin_url:
            score += 0.05
        return min(score, 1.0)  # Cap at 1.0

    def scrape_all_companies(self) -> List[Company]:
        """Scrape information for all target companies"""
        self.logger.info(f"Scraping {len(self.target_companies)} companies...")
        companies = []
        for company_name in self.target_companies:
            try:
                company = self.scrape_company_info(company_name)
                companies.append(company)
                # Rate limiting
                time.sleep(2)
                self.logger.info(f"Processed {company.name} - Score: {company.qualification_score:.2f}")
            except Exception as e:
                self.logger.error(f"Error processing {company_name}: {e}")
                continue
        # Sort by qualification score
        companies.sort(key=lambda x: x.qualification_score, reverse=True)
        return companies

    def get_companies_by_event(self, event_name: str) -> List[Company]:
        """Get companies likely to attend specific event"""
        all_companies = self.scrape_all_companies()
        # Filter companies most likely to attend this event type
        event_lower = event_name.lower()
        if 'sign' in event_lower or 'expo' in event_lower:
            # Prioritize signage-focused companies
            relevant_companies = [c for c in all_companies
                                  if any(word in c.industry.lower()
                                         for word in ['signage', 'graphics', 'visual'])]
        elif 'print' in event_lower:
            # Prioritize printing companies
            relevant_companies = [c for c in all_companies
                                  if any(word in c.industry.lower()
                                         for word in ['printing', 'digital', 'wide format'])]
        else:
            relevant_companies = all_companies
        return relevant_companies[:10]  # Return top 10 most relevant

    def save_companies_to_csv(self, companies: List[Company], filename: str = "data/companies.csv"):
        """Save companies to CSV file"""
        try:
            companies_data = []
            for company in companies:
                companies_data.append({
                    'name': company.name,
                    'website': company.website,
                    'industry': company.industry,
                    'size': company.size,
                    'revenue': company.revenue,
                    'location': company.location,
                    'description': company.description[:200],
                    'linkedin_url': company.linkedin_url,
                    'technologies': '; '.join(company.technologies),
                    'recent_news': '; '.join(company.recent_news),
                    'qualification_score': company.qualification_score
                })
            df = pd.DataFrame(companies_data)
            df.to_csv(filename, index=False)
            self.logger.info(f"Saved {len(companies)} companies to {filename}")
        except Exception as e:
            self.logger.error(f"Error saving companies to CSV: {e}")

if __name__ == "__main__":
    scraper = CompanyScraper()
    companies = scraper.scrape_all_companies()
    scraper.save_companies_to_csv(companies)
    print(f"\nTop 5 Qualified Companies:")
    for company in companies[:5]:
        print(f"- {company.name}")
        print(f" Score: {company.qualification_score:.2f}")
        print(f" Industry: {company.industry}")
        print(f" Size: {company.size}")
        print()