"""Parsing utilities for agent skill outputs."""

import json
import re

from sentinelcx.models.response import ComplianceFlag, ComplianceResult
from sentinelcx.models.ticket import SentimentScore


def parse_sentiment_output(text: str) -> SentimentScore:
    """Parse structured sentiment JSON from agent output.

    Searches for a JSON block in the text and extracts sentiment fields.
    """
    # Try to find JSON in the text (may be wrapped in markdown code blocks)
    json_match = re.search(r"\{[^{}]*\"score\"[^{}]*\}", text, re.DOTALL)
    if json_match:
        data = json.loads(json_match.group())
        return SentimentScore(
            score=data.get("score", 0.5),
            label=data.get("label", "unknown"),
            confidence=data.get("confidence", 0.5),
            indicators=data.get("indicators", []),
        )
    # Fallback: return neutral sentiment
    return SentimentScore(score=0.5, label="unknown", confidence=0.0, indicators=[])


def parse_compliance_output(text: str) -> ComplianceResult:
    """Parse structured compliance JSON from agent output."""
    # Find JSON that contains "passed" — may have nested objects/arrays
    # Try progressively larger substrings starting from "passed"
    idx = text.find('"passed"')
    if idx == -1:
        return ComplianceResult(passed=True, flags=[])
    # Walk back to find opening brace
    start = text.rfind("{", 0, idx)
    if start == -1:
        return ComplianceResult(passed=True, flags=[])
    # Try to parse from start to progressively later closing braces
    data = None
    for end in range(start + 1, len(text) + 1):
        if text[end - 1] == "}":
            try:
                data = json.loads(text[start:end])
                break
            except json.JSONDecodeError:
                continue
    if data is not None:
        flags = [
            ComplianceFlag(
                field=f.get("field", "unknown"),
                issue=f.get("issue", ""),
                severity=f.get("severity", "warning"),
            )
            for f in data.get("flags", [])
        ]
        return ComplianceResult(passed=data.get("passed", True), flags=flags)
    return ComplianceResult(passed=True, flags=[])


# Compiled regex patterns for common PII detection
PII_PATTERNS = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"),
    "email_internal": re.compile(r"\b[a-zA-Z0-9._%+-]+@(internal|corp|company)\.\w+\b"),
    "api_key": re.compile(r"\b(sk-|api[_-]key[=:]\s*)[a-zA-Z0-9]{20,}\b", re.IGNORECASE),
}


def validate_response_text(text: str) -> ComplianceResult:
    """Rule-based pre-check for PII in response text.

    This runs before the agent-based compliance scan as a fast first pass.
    """
    flags = []
    for pii_type, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            flags.append(
                ComplianceFlag(
                    field="pii",
                    issue=f"Potential {pii_type} detected in response",
                    severity="critical",
                )
            )

    return ComplianceResult(passed=len(flags) == 0, flags=flags)
