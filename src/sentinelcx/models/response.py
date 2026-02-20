"""Response and compliance models."""

from datetime import datetime

from pydantic import BaseModel, Field


class ComplianceFlag(BaseModel):
    field: str
    issue: str
    severity: str = "warning"


class ComplianceResult(BaseModel):
    passed: bool = True
    flags: list[ComplianceFlag] = Field(default_factory=list)
    reviewed_at: datetime = Field(default_factory=datetime.utcnow)


class DraftResponse(BaseModel):
    content: str
    sources: list[str] = Field(default_factory=list)
    compliance: ComplianceResult = Field(default_factory=ComplianceResult)
    confidence: float = Field(ge=0.0, le=1.0, default=0.0)


class EscalationSummary(BaseModel):
    ticket_id: str
    customer_context: str = ""
    issue_summary: str = ""
    attempted_actions: list[str] = Field(default_factory=list)
    recommended_assignee: str = ""
    urgency: str = "medium"
