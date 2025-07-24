import openai
import os
import json
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import asdict
import time
import re
import sys

# Import our models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.models import Company, Event, Stakeholder, Lead

class LeadQualifier:
    def __init__(self, api_key: str = None):
        self.logger = self._setup_logging()
        # Initialize OpenAI client
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            # Try to get from environment
            self.client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # DuPont Tedlar ICP criteria
        self.icp_criteria = {
            "target_industries": [
                "Signage & Graphics", "Specialty Films", "Protective Coatings",
                "Automotive Graphics", "Architectural Films", "Industrial Graphics",
                "Digital Printing", "Wide Format Printing", "Vehicle Wraps"
            ],
            "company_size_preference": "Medium to Large (100+ employees)",
            "revenue_threshold": "$10M+",
            "technology_focus": [
                "Protective Films", "Weather-resistant Materials", "UV Protection",
                "Chemical Resistance", "Durability Solutions", "Outdoor Applications"
            ],
            "decision_maker_titles": [
                "VP Product Development", "Director Innovation", "R&D Manager",
                "Chief Technology Officer", "VP Operations", "Director Materials",
                "VP Marketing", "Product Manager", "Technical Director"
            ]
        }

    def _setup_logging(self):
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)

    def qualify_company(self, company: Company, event: Event = None) -> Tuple[float, str]:
        """
        Qualify a company using AI analysis and rule-based scoring
        Returns: (qualification_score, rationale)
        """
        try:
            # Base scoring using rules
            base_score, base_rationale = self._calculate_base_score(company)
            # Enhanced AI analysis
            ai_score, ai_rationale = self._ai_qualify_company(company, event)
            # Combine scores (weighted average)
            final_score = (base_score * 0.4) + (ai_score * 0.6)
            # Combine rationales
            final_rationale = f"{ai_rationale}\n\nScoring Details: {base_rationale}"
            return min(final_score, 1.0), final_rationale
        except Exception as e:
            self.logger.error(f"Error qualifying company {company.name}: {e}")
            # Fallback to rule-based only
            return self._calculate_base_score(company)

    def _calculate_base_score(self, company: Company) -> Tuple[float, str]:
        """Rule-based qualification scoring"""
        score = 0.0
        rationale_points = []

        # Industry fit (25% of score)
        industry_score = 0.0
        if company.industry:
            for target_industry in self.icp_criteria["target_industries"]:
                if any(word in company.industry.lower() for word in target_industry.lower().split()):
                    industry_score = 0.25
                    rationale_points.append(f"Strong industry alignment ({company.industry})")
                    break
            if industry_score == 0:
                # Partial matches
                graphics_keywords = ['graphics', 'printing', 'visual', 'display', 'sign']
                if any(word in company.industry.lower() for word in graphics_keywords):
                    industry_score = 0.15
                    rationale_points.append(f"Moderate industry relevance ({company.industry})")
        score += industry_score

        # Company size (20% of score)
        size_score = 0.0
        if company.size:
            if 'large' in company.size.lower():
                size_score = 0.20
                rationale_points.append(f"Ideal company size ({company.size})")
            elif 'medium' in company.size.lower():
                size_score = 0.15
                rationale_points.append(f"Good company size ({company.size})")
            elif any(num in company.size for num in ['100+', '500+', '1000+']):
                size_score = 0.12
                rationale_points.append(f"Adequate company size ({company.size})")
        score += size_score

        # Revenue potential (20% of score)
        revenue_score = 0.0
        if company.revenue:
            revenue_lower = company.revenue.lower()
            if '$' in revenue_lower:
                if 'b' in revenue_lower or 'billion' in revenue_lower:
                    revenue_score = 0.20
                    rationale_points.append(f"High revenue potential ({company.revenue})")
                elif 'm' in revenue_lower or 'million' in revenue_lower:
                    # Extract number to determine score
                    numbers = re.findall(r'\d+', company.revenue)
                    if numbers:
                        amount = int(numbers[0])
                        if amount >= 100:
                            revenue_score = 0.18
                        elif amount >= 50:
                            revenue_score = 0.15
                        elif amount >= 10:
                            revenue_score = 0.12
                    rationale_points.append(f"Revenue meets threshold ({company.revenue})")
        score += revenue_score

        # Technology alignment (15% of score)
        tech_score = 0.0
        if company.technologies:
            relevant_tech_count = 0
            for tech in company.technologies:
                for focus_area in self.icp_criteria["technology_focus"]:
                    if any(word in tech.lower() for word in focus_area.lower().split()):
                        relevant_tech_count += 1
                        break
            if relevant_tech_count > 0:
                tech_score = min(relevant_tech_count * 0.05, 0.15)
                rationale_points.append(f"Technology alignment: {relevant_tech_count} relevant technologies")
        score += tech_score

        # Market activity (10% of score)
        activity_score = 0.0
        if company.recent_news:
            innovation_keywords = ['launch', 'new', 'expand', 'partnership', 'investment', 'growth']
            relevant_news = 0
            for news in company.recent_news:
                if any(keyword in news.lower() for keyword in innovation_keywords):
                    relevant_news += 1
            if relevant_news > 0:
                activity_score = min(relevant_news * 0.03, 0.10)
                rationale_points.append(f"Recent market activity: {relevant_news} relevant developments")
        score += activity_score

        # Digital presence (10% of score)
        presence_score = 0.0
        if company.website:
            presence_score += 0.03
        if company.linkedin_url:
            presence_score += 0.07
            rationale_points.append("Strong digital presence")
        score += presence_score

        # Compile rationale
        if not rationale_points:
            rationale_points.append("Limited qualification data available")
        rationale = ". ".join(rationale_points)
        return score, rationale

    def _ai_qualify_company(self, company: Company, event: Event = None) -> Tuple[float, str]:
        """Use AI to analyze company qualification with enhanced context"""
        try:
            dupont_context = """
DuPont Tedlar is a high-performance protective film used in graphics and signage applications.
Key value propositions:
- Superior weather resistance and UV protection
- Chemical resistance for outdoor applications
- Extends graphic life by 40%+ compared to unprotected films
- Premium solution for demanding environments
- Applications: Vehicle wraps, outdoor signage, architectural graphics, industrial graphics
Target customers are companies that:
- Manufacture or apply graphics/signage materials
- Need long-lasting, weather-resistant solutions
- Serve outdoor/automotive/architectural markets
- Value premium performance over low cost
"""

            # Prepare company data
            company_data = {
                "name": company.name,
                "industry": company.industry,
                "size": company.size,
                "revenue": company.revenue,
                "location": company.location,
                "description": company.description,
                "technologies": company.technologies,
                "recent_news": company.recent_news
            }
            event_context = ""
            if event:
                event_context = f"""
Event Context: This company is being evaluated for outreach at {event.name}
({event.date}) in {event.location}. Event focus: {event.industry}.
"""

            prompt = f"""
{dupont_context}
{event_context}
Analyze this company for qualification as a lead for DuPont Tedlar's Graphics & Signage team:
Company Data:
{json.dumps(company_data, indent=2)}
Please provide:
1. A qualification score from 0.0 to 1.0 (where 1.0 is perfect fit)
2. A detailed rationale explaining why this company is/isn't a good fit
Consider:
- Industry alignment with graphics/signage/protective films
- Company size and market reach potential
- Technology needs that align with Tedlar benefits
- Market positioning and customer base
- Growth trajectory and innovation focus
Format your response as JSON:
{{
"score": 0.XX,
"rationale": "Detailed explanation of qualification assessment..."
}}
"""
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a B2B sales qualification expert specializing in the graphics and signage industry. Provide accurate, data-driven assessments."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            # Parse response
            response_text = response.choices[0].message.content
            # Try to extract JSON
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                return float(result.get("score", 0.5)), result.get("rationale", "AI analysis completed")
            else:
                # Fallback parsing
                lines = response_text.split('\n')
                score = 0.5
                rationale = response_text
                for line in lines:
                    if 'score' in line.lower() and any(char.isdigit() for char in line):
                        numbers = re.findall(r'\d+\.?\d*', line)
                        if numbers:
                            score = min(float(numbers[0]), 1.0)
                            break
                return score, rationale

        except json.JSONDecodeError:
            # Fallback to simple parsing
            return 0.5, response_text
        except Exception as e:
            self.logger.warning(f"AI qualification failed for {company.name}: {e}")
            return 0.5, "AI analysis unavailable, using rule-based scoring"

    def identify_decision_makers(self, company: Company) -> List[Stakeholder]:
        """Identify likely decision makers at the company"""
        try:
            prompt = f"""
Based on this company profile, identify the most likely decision makers for purchasing
protective film solutions for graphics/signage applications:
Company: {company.name}
Industry: {company.industry}
Size: {company.size}
Description: {company.description}
Technologies: {', '.join(company.technologies) if company.technologies else 'Not specified'}
Suggest 3–5 likely decision maker titles and departments for DuPont Tedlar sales outreach.
Focus on roles that would evaluate protective film solutions for graphics applications.
Format as JSON array:
[
{{
  "title": "VP Product Development",
  "department": "Product Development",
  "decision_maker_score": 0.9,
  "reasoning": "Key stakeholder for material selection decisions"
}}
]
"""

            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a B2B sales expert who identifies decision makers in graphics/signage companies."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.2,
                max_tokens=600
            )

            response_text = response.choices[0].message.content

            # Parse JSON response
            json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON array found in AI response")

            decision_makers_data = json.loads(json_match.group())
            stakeholders = []
            for dm in decision_makers_data:
                stakeholders.append(Stakeholder(
                    name="[To be identified via LinkedIn Sales Navigator]",
                    title=dm.get("title", ""),
                    department=dm.get("department", ""),
                    linkedin_url="", # placeholder
                    email="",
                    phone="",
                    decision_maker_score=dm.get("decision_maker_score", 0.5),
                    contact_method="linkedin"
                ))
            return stakeholders

        except Exception as e:
            self.logger.warning(f"Failed to identify decision makers for {company.name}: {e}")
            return []

    def qualify_lead(self, company_dict: Dict, event: Optional[Event] = None) -> Dict:
        """Convert dict to Company, qualify it, return score/rationale/is_qualified"""
        try:
            company = Company(
                name=company_dict.get("name", ""),
                website=company_dict.get("website", ""),
                industry=company_dict.get("industry", ""),
                size=company_dict.get("size", ""),
                revenue=company_dict.get("revenue", ""),
                location=company_dict.get("location", ""),
                description=company_dict.get("description", ""),
                linkedin_url=company_dict.get("linkedin_url", ""),
                technologies=company_dict.get("technologies", []),
                recent_news=company_dict.get("recent_news", []),
                key_contacts=company_dict.get("key_contacts", [])
            )

            score, rationale = self.qualify_company(company, event)

            return {
                "score": score,
                "rationale": rationale,
                "is_qualified": score >= 0.7,
                "industry_alignment": company.industry
            }

        except Exception as e:
            self.logger.error(f"Failed to qualify lead {company_dict.get('name', 'Unknown')}: {e}")
            return {
                "score": 0.0,
                "rationale": "Error during qualification",
                "is_qualified": False,
                "industry_alignment": ""
            }