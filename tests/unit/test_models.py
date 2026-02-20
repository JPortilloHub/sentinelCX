"""Tests for Pydantic data models."""

import pytest
from pydantic import ValidationError

from sentinelcx.models.customer import AccountHealth, CaseHistory, Customer, PurchaseHistory
from sentinelcx.models.response import (
    ComplianceFlag,
    ComplianceResult,
    DraftResponse,
    EscalationSummary,
)
from sentinelcx.models.ticket import (
    SentimentScore,
    Ticket,
    TicketCategory,
    TicketPriority,
    TriageDecision,
    TriageResult,
)


class TestTicketModels:
    def test_ticket_priority_values(self):
        assert TicketPriority.LOW == "low"
        assert TicketPriority.URGENT == "urgent"

    def test_ticket_category_values(self):
        assert TicketCategory.BILLING == "billing"
        assert TicketCategory.TECHNICAL == "technical"

    def test_triage_decision_values(self):
        assert TriageDecision.AUTO_HANDLE == "auto_handle"
        assert TriageDecision.ESCALATE == "escalate"

    def test_sentiment_score_valid(self):
        score = SentimentScore(
            score=0.7, label="frustrated", confidence=0.9, indicators=["ALL CAPS"]
        )
        assert score.score == 0.7
        assert score.indicators == ["ALL CAPS"]

    def test_sentiment_score_bounds(self):
        with pytest.raises(ValidationError):
            SentimentScore(score=1.5, label="x", confidence=0.5)
        with pytest.raises(ValidationError):
            SentimentScore(score=-0.1, label="x", confidence=0.5)

    def test_triage_result(self):
        result = TriageResult(
            decision=TriageDecision.NEEDS_RESEARCH,
            category=TicketCategory.TECHNICAL,
            priority=TicketPriority.HIGH,
            sentiment=SentimentScore(score=0.5, label="mild", confidence=0.8),
            confidence=0.75,
            reasoning="Needs KB lookup",
        )
        assert result.decision == "needs_research"
        assert result.priority == "high"

    def test_ticket_defaults(self):
        ticket = Ticket(id="1", conversation_id="conv-1")
        assert ticket.subject == ""
        assert ticket.metadata == {}


class TestCustomerModels:
    def test_customer_creation(self):
        customer = Customer(id="1", name="Test", email="t@t.com", account_id="acc-1")
        assert customer.tier == "standard"

    def test_account_health_bounds(self):
        health = AccountHealth(score=85.5, churn_risk="low", lifetime_value=10000)
        assert health.score == 85.5

    def test_purchase_history_defaults(self):
        ph = PurchaseHistory()
        assert ph.items == []
        assert ph.total_spent == 0.0

    def test_case_history_defaults(self):
        ch = CaseHistory()
        assert ch.cases == []
        assert ch.resolution_rate == 0.0


class TestResponseModels:
    def test_compliance_flag(self):
        flag = ComplianceFlag(field="pii", issue="SSN detected", severity="critical")
        assert flag.severity == "critical"

    def test_compliance_result_passing(self):
        result = ComplianceResult()
        assert result.passed is True
        assert result.flags == []

    def test_compliance_result_failing(self):
        result = ComplianceResult(
            passed=False,
            flags=[ComplianceFlag(field="pii", issue="test", severity="critical")],
        )
        assert not result.passed
        assert len(result.flags) == 1

    def test_draft_response(self):
        resp = DraftResponse(content="Hello!", sources=["doc.md"], confidence=0.9)
        assert resp.compliance.passed is True

    def test_escalation_summary(self):
        summary = EscalationSummary(
            ticket_id="T-1",
            issue_summary="Complex billing issue",
            urgency="high",
        )
        assert summary.attempted_actions == []
