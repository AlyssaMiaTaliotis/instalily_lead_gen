import sys
import os
import pytest
from datetime import datetime

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.ai_engine.outreach_generator import OutreachGenerator

@pytest.fixture
def sample_lead():
    return {
        "company_name": "SignsPro",
        "contact_name": "Jane Smith",
        "contact_title": "Director of Product Innovation",
        "company_description": "Leading provider of outdoor signage materials.",
        "industry_alignment": "Outdoor signage and wraps",
        "event_context": "ISA Sign Expo 2025 in Las Vegas",
        "qualification_score": 0.85,
        "company_size": "Medium (200-500 employees)",
        "linkedin_profile": "https://linkedin.com/in/janesmith"
    }

def test_generate_outreach_with_mock(monkeypatch, sample_lead):
    from backend.ai_engine.outreach_generator import OutreachGenerator

    class MockChatResponse:
        def __init__(self, message_text):
            self.choices = [type('Obj', (object,), {"message": type('Msg', (object,), {"content": message_text})()})]

    def mock_chat_create(*args, **kwargs):
        prompt = kwargs['messages'][-1]['content']
        if "subject lines" in prompt.lower():
            return MockChatResponse("1. Let's talk signage\n2. Boosting graphic durability\n3. Is ISA the right fit?")
        elif "follow-up" in prompt.lower():
            return MockChatResponse("FOLLOW-UP 1:\nJust checking in.\n\nFOLLOW-UP 2:\nFinal quick touch base.")
        else:
            return MockChatResponse("Hi Jane, I saw that SignsPro will be at ISA Sign Expo...")

    generator = OutreachGenerator(api_key="fake-key")

    # Patch
    monkeypatch.setattr(generator.client.chat.completions, "create", mock_chat_create)

    result = generator.generate_personalized_outreach(sample_lead)

    assert result["success"] is True
    data = result["data"]
    assert "primary_message" in data
    assert "subject_line" in data
    assert "follow_up_sequence" in data
    assert isinstance(data["personalization_elements"], dict)
    assert data["message_type"] == "cold_outreach"
    assert datetime.fromisoformat(data["generated_at"])


def test_validate_outreach_content():
    generator = OutreachGenerator(api_key="fake")

    fake_outreach = {
        "primary_message": "Get a FREE demo now! Act fast! Guaranteed results! Limited time only!",
        "personalization_elements": {}
    }

    validation = generator.validate_outreach_content(fake_outreach)
    assert validation["is_valid"] is False
    assert any("spam" in w.lower() for w in validation["warnings"])

def test_validate_good_outreach():
    generator = OutreachGenerator(api_key="fake")

    outreach = {
        "primary_message": (
            "Hi Jane, I noticed SignsPro is attending ISA Sign Expo. "
            "Given your leadership in product innovation, I thought you'd be interested in how DuPont Tedlar's protective films "
            "can enhance graphic durability and reduce maintenance. Let me know if you'd be open to a quick chat next week!"
        ),
        "personalization_elements": {
            "company_reference": "SignsPro",
            "role_relevance": "Director of Product Innovation",
            "industry_context": "Outdoor signage",
            "event_mention": "ISA Sign Expo",
            "size_consideration": "Medium"
        }
    }

    validation = generator.validate_outreach_content(outreach)
    assert validation["is_valid"] is True
    assert "too brief" not in " ".join(validation["warnings"]).lower()