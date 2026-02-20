"""Shared test fixtures and mock clients."""

import pytest

from sentinelcx.config import (
    ChatwootSettings,
    KnowledgeBaseSettings,
    SalesforceSettings,
    Settings,
    SlackSettings,
)


@pytest.fixture
def mock_settings(tmp_path):
    """Settings with dummy values for testing."""
    kb_path = tmp_path / "knowledge_base"
    kb_path.mkdir()
    cache_dir = tmp_path / "embedding_cache"
    cache_dir.mkdir()

    return Settings(
        anthropic_api_key="test-api-key",
        salesforce=SalesforceSettings(
            username="test@example.com",
            password="testpass",
            security_token="testtoken",
            domain="test",
        ),
        chatwoot=ChatwootSettings(
            base_url="http://localhost:3000",
            api_token="test-token",
            account_id=1,
        ),
        slack=SlackSettings(
            bot_token="xoxb-test-token",
            signing_secret="test-secret",
            escalation_channel="#test-escalations",
        ),
        knowledge_base=KnowledgeBaseSettings(
            knowledge_base_path=str(kb_path),
            embedding_model_name="all-MiniLM-L6-v2",
            embedding_cache_dir=str(cache_dir),
        ),
    )


@pytest.fixture
def sample_ticket():
    """A sample ticket dict for testing."""
    return {
        "id": "TICKET-0001",
        "conversation_id": "1",
        "customer_id": "CUST-0001",
        "subject": "Can't log in to my account",
        "body": "I've been trying to log in for the past hour and keep getting an error.",
        "expected_category": "technical",
        "expected_priority": "high",
    }


@pytest.fixture
def sample_customer():
    """A sample customer dict for testing."""
    return {
        "id": "CUST-0001",
        "account_id": "ACC-0001",
        "name": "Sarah Johnson",
        "email": "sarah.johnson@example.com",
        "tier": "premium",
    }
