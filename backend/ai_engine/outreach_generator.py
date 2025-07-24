import openai
import logging
from typing import Dict, List, Optional
import json
from datetime import datetime
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OutreachGenerator:
    def __init__(self, api_key: str):
        """Initialize the outreach message generator"""
        openai.api_key = api_key
        self.client = openai.OpenAI(api_key=api_key)

    def generate_personalized_outreach(self, lead_data: Dict) -> Dict:
        """
        Generate personalized outreach message for a qualified lead
        Args:
            lead_data: Dictionary containing lead information
            - company_name: str
            - contact_name: str
            - contact_title: str
            - company_description: str
            - industry_alignment: str
            - event_context: str
            - qualification_score: float
            - company_size: str
            - linkedin_profile: str (optional)
        Returns:
            Dictionary with generated outreach content
        """
        try:
            # Create context-aware prompt
            prompt = self._build_outreach_prompt(lead_data)
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert sales outreach specialist for DuPont Tedlar,
specializing in protective films for graphics and signage applications.
Your goal is to create compelling, personalized outreach messages that:
1. Reference specific industry context
2. Highlight relevant Tedlar benefits
3. Are professional but not overly salesy
4. Include a clear but soft call-to-action
5. Are concise (under 200 words)"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=300
            )
            outreach_content = response.choices[0].message.content.strip()
            # Generate subject line
            subject_line = self._generate_subject_line(lead_data)
            # Generate follow-up sequence
            follow_ups = self._generate_follow_up_sequence(lead_data, outreach_content)
            return {
                "success": True,
                "data": {
                    "primary_message": outreach_content,
                    "subject_line": subject_line,
                    "follow_up_sequence": follow_ups,
                    "personalization_elements": self._extract_personalization_elements(lead_data),
                    "generated_at": datetime.now().isoformat(),
                    "message_type": "cold_outreach"
                }
            }
        except Exception as e:
            logger.error(f"Error generating outreach for {lead_data.get('company_name', 'Unknown')}: {str(e)}")
            return {
                "success": False,
                "error": f"Failed to generate outreach: {str(e)}",
                "fallback_message": self._generate_fallback_message(lead_data)
            }

    def _build_outreach_prompt(self, lead_data: Dict) -> str:
        """Build context-rich prompt for outreach generation"""
        company_name = lead_data.get('company_name', 'the company')
        contact_name = lead_data.get('contact_name', 'there')
        contact_title = lead_data.get('contact_title', 'team member')
        industry_alignment = lead_data.get('industry_alignment', '')
        event_context = lead_data.get('event_context', '')
        company_size = lead_data.get('company_size', '')
        prompt = f"""
Generate a personalized LinkedIn/email outreach message for:
CONTACT DETAILS:
- Name: {contact_name}
- Title: {contact_title}
- Company: {company_name}
- Company Size: {company_size}
CONTEXT & RELEVANCE:
- Industry Alignment: {industry_alignment}
- Event Context: {event_context}
DUPONT TEDLAR VALUE PROPOSITIONS TO CONSIDER:
- Weather resistance and UV protection for outdoor graphics
- Enhanced durability extending graphic lifespan
- Superior adhesion properties for various substrates
- Cost savings through reduced replacement frequency
- Sustainability benefits through longer-lasting graphics
INSTRUCTIONS:
1. Start with a relevant industry observation or event reference
2. Briefly mention how Tedlar could solve their specific challenges
3. Include a soft ask for a brief conversation
4. Keep it conversational and authentic
5. Avoid overly promotional language
Generate the outreach message:
"""
        return prompt

    def _generate_subject_line(self, lead_data: Dict) -> str:
        """Generate compelling subject line"""
        try:
            company_name = lead_data.get('company_name', 'your company')
            event_context = lead_data.get('event_context', '')
            subject_prompt = f"""
Generate 3 compelling email subject lines for outreach to {company_name}.
Context: {event_context}
Make them:
1. Professional but intriguing
2. Reference industry/event context when relevant
3. Under 50 characters
4. Avoid spam trigger words
Return only the 3 subject lines, numbered 1-3.
"""
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": subject_prompt}],
                temperature=0.8,
                max_tokens=100
            )
            subject_lines = response.choices[0].message.content.strip().split('\n')
            # Return the first subject line (remove numbering)
            if subject_lines:
                return subject_lines[0].split('. ', 1)[-1] if '. ' in subject_lines[0] else subject_lines[0]
        except Exception as e:
            logger.error(f"Error generating subject line: {str(e)}")
        # Fallback subject lines
        fallbacks = [
            f"Enhancing durability for {lead_data.get('company_name', 'your graphics')}",
            "Quick question about your outdoor signage",
            "Extending graphic lifespan - worth a chat?"
        ]
        return fallbacks[0]

    def _generate_follow_up_sequence(self, lead_data: Dict, initial_message: str) -> List[Dict]:
        """Generate a sequence of follow-up messages"""
        try:
            follow_up_prompt = f"""
Based on this initial outreach message to {lead_data.get('company_name', '')}:
"{initial_message}"
Generate 2 brief follow-up messages for if they don't respond:
1. Follow-up #1 (after 1 week): Add new value/insight
2. Follow-up #2 (after 2 weeks): Final gentle touchpoint
Each follow-up should:
- Be shorter than the original (under 100 words)
- Add new value or perspective
- Reference the original message subtly
- Maintain professional tone
Format as:
FOLLOW-UP 1:
[message]
FOLLOW-UP 2:
[message]
"""
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": follow_up_prompt}],
                temperature=0.7,
                max_tokens=200
            )
            content = response.choices[0].message.content.strip()
            # Parse follow-ups
            follow_ups = []
            parts = content.split('FOLLOW-UP')
            for i, part in enumerate(parts[1:], 1):  # Skip first empty part
                message = part.split(':', 1)[-1].strip()
                follow_ups.append({
                    "sequence": i,
                    "timing": f"{i} week{'s' if i > 1 else ''} after initial",
                    "message": message,
                    "type": "follow_up"
                })
            return follow_ups
        except Exception as e:
            logger.error(f"Error generating follow-ups: {str(e)}")
            return []

    def _extract_personalization_elements(self, lead_data: Dict) -> Dict:
        """Extract key personalization elements used"""
        return {
            "company_reference": lead_data.get('company_name', ''),
            "role_relevance": lead_data.get('contact_title', ''),
            "industry_context": lead_data.get('industry_alignment', ''),
            "event_mention": lead_data.get('event_context', ''),
            "size_consideration": lead_data.get('company_size', ''),
        }

    def _generate_fallback_message(self, lead_data: Dict) -> str:
        """Generate simple fallback message if AI generation fails"""
        company_name = lead_data.get('company_name', 'your company')
        contact_name = lead_data.get('contact_name', 'Hello')
        return f"""Hi {contact_name},

I came across {company_name} and was impressed by your work in the graphics and signage space.

At DuPont, our Tedlar protective films help companies like yours extend the lifespan of outdoor graphics while reducing maintenance costs through superior weather resistance and UV protection.

Would you be open to a brief conversation about how this might benefit your current projects?

Best regards,
DuPont Tedlar Team"""

    def generate_bulk_outreach(self, leads: List[Dict]) -> List[Dict]:
        """Generate outreach for multiple leads"""
        results = []
        for i, lead in enumerate(leads):
            logger.info(f"Generating outreach {i+1}/{len(leads)} for {lead.get('company_name', 'Unknown')}")
            result = self.generate_personalized_outreach(lead)
            result['lead_id'] = lead.get('id', i)
            results.append(result)
            # Add delay to respect API limits
            if i < len(leads) - 1:
                time.sleep(1)  # 1 second delay between requests
        return results

    def validate_outreach_content(self, outreach_data: Dict) -> Dict:
        """Validate generated outreach content"""
        validation_results = {
            "is_valid": True,
            "warnings": [],
            "suggestions": []
        }
        message = outreach_data.get('primary_message', '')
        # Check message length
        if len(message) > 1000:
            validation_results["warnings"].append("Message might be too long for initial outreach")
        elif len(message) < 100:
            validation_results["warnings"].append("Message might be too brief")
        # Check for spam triggers
        spam_triggers = ['free', 'guaranteed', 'limited time', 'act now', 'urgent']
        found_triggers = [trigger for trigger in spam_triggers if trigger.lower() in message.lower()]
        if found_triggers:
            validation_results["warnings"].append(f"Contains potential spam triggers: {', '.join(found_triggers)}")
        # Check for personalization
        if not any(element for element in outreach_data.get('personalization_elements', {}).values()):
            validation_results["warnings"].append("Low personalization detected")
        # Set validity
        validation_results["is_valid"] = len(validation_results["warnings"]) < 3
        return validation_results