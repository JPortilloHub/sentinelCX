"""Customer-related models."""

from datetime import datetime

from pydantic import BaseModel, Field


class Customer(BaseModel):
    id: str
    name: str
    email: str
    account_id: str
    tier: str = "standard"


class AccountHealth(BaseModel):
    score: float = Field(ge=0.0, le=100.0, description="Account health 0-100")
    churn_risk: str = "low"
    lifetime_value: float = 0.0
    last_interaction: datetime | None = None


class PurchaseHistory(BaseModel):
    items: list[dict] = Field(default_factory=list)
    total_spent: float = 0.0
    last_purchase_date: datetime | None = None


class CaseHistory(BaseModel):
    cases: list[dict] = Field(default_factory=list)
    resolution_rate: float = 0.0
    avg_resolution_time_hours: float = 0.0
