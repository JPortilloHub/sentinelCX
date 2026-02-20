"""Tests for skill loader and utilities."""

import pytest

from sentinelcx.skills import list_skills, load_skill
from sentinelcx.skills.utils import (
    PII_PATTERNS,
    parse_compliance_output,
    parse_sentiment_output,
    validate_response_text,
)


class TestSkillLoader:
    def test_load_sentiment_analysis(self):
        content = load_skill("sentiment_analysis")
        assert "Sentiment Analysis Skill" in content
        assert "frustration" in content.lower()

    def test_load_product_knowledge(self):
        content = load_skill("product_knowledge")
        assert "Product Knowledge Skill" in content
        assert "search_knowledge_base" in content

    def test_load_compliance_check(self):
        content = load_skill("compliance_check")
        assert "Compliance Check Skill" in content
        assert "PII" in content

    def test_load_nonexistent_skill(self):
        with pytest.raises(FileNotFoundError):
            load_skill("nonexistent_skill")

    def test_list_skills(self):
        skills = list_skills()
        assert "sentiment_analysis" in skills
        assert "product_knowledge" in skills
        assert "compliance_check" in skills


class TestSentimentParsing:
    def test_parse_valid_json(self):
        text = (
            '{"score": 0.7, "label": "frustrated", "confidence": 0.9, "indicators": ["ALL CAPS"]}'
        )
        result = parse_sentiment_output(text)
        assert result.score == 0.7
        assert result.label == "frustrated"
        assert "ALL CAPS" in result.indicators

    def test_parse_json_in_markdown(self):
        text = """Here is my analysis:
```json
{"score": 0.3, "label": "mild", "confidence": 0.85, "indicators": []}
```"""
        result = parse_sentiment_output(text)
        assert result.score == 0.3

    def test_parse_no_json(self):
        result = parse_sentiment_output("No JSON here")
        assert result.score == 0.5
        assert result.confidence == 0.0

    def test_parse_partial_json(self):
        text = '{"score": 0.8, "label": "angry", "confidence": 0.6}'
        result = parse_sentiment_output(text)
        assert result.score == 0.8
        assert result.indicators == []


class TestComplianceParsing:
    def test_parse_passing(self):
        text = '{"passed": true, "flags": []}'
        result = parse_compliance_output(text)
        assert result.passed is True
        assert result.flags == []

    def test_parse_failing(self):
        text = '{"passed": false, "flags": [{"field": "pii", "issue": "SSN found", "severity": "critical"}]}'
        result = parse_compliance_output(text)
        assert result.passed is False
        assert len(result.flags) == 1
        assert result.flags[0].severity == "critical"


class TestPIIDetection:
    def test_ssn_pattern(self):
        assert PII_PATTERNS["ssn"].search("SSN: 123-45-6789")
        assert not PII_PATTERNS["ssn"].search("Phone: 123-456-7890")

    def test_credit_card_pattern(self):
        assert PII_PATTERNS["credit_card"].search("Card: 4111 1111 1111 1111")
        assert PII_PATTERNS["credit_card"].search("Card: 4111-1111-1111-1111")

    def test_validate_clean_text(self):
        result = validate_response_text("Thank you for contacting us. We'll help you right away.")
        assert result.passed is True

    def test_validate_ssn_in_text(self):
        result = validate_response_text("Your SSN is 123-45-6789, right?")
        assert result.passed is False
        assert any(f.field == "pii" for f in result.flags)

    def test_validate_credit_card_in_text(self):
        result = validate_response_text("Your card number 4111 1111 1111 1111 has been charged.")
        assert result.passed is False
