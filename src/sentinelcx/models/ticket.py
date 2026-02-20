"""Ticket-related models and enums."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class TicketPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TicketCategory(StrEnum):
    BILLING = "billing"
    TECHNICAL = "technical"
    ACCOUNT = "account"
    PRODUCT = "product"
    GENERAL = "general"


class TriageDecision(StrEnum):
    AUTO_HANDLE = "auto_handle"
    NEEDS_RESEARCH = "needs_research"
    ESCALATE = "escalate"


class SentimentScore(BaseModel):
    score: float = Field(ge=0.0, le=1.0, description="Frustration level 0-1")
    label: str = Field(description="Human-readable sentiment label")
    confidence: float = Field(ge=0.0, le=1.0, description="Classification confidence")
    indicators: list[str] = Field(default_factory=list, description="Detected sentiment indicators")


class TriageResult(BaseModel):
    decision: TriageDecision
    category: TicketCategory
    priority: TicketPriority
    sentiment: SentimentScore
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning: str = ""


class Ticket(BaseModel):
    id: str
    conversation_id: str
    customer_id: str | None = None
    subject: str = ""
    body: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)
