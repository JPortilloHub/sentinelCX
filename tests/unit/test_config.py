"""Tests for configuration loading."""

from sentinelcx.config import (
    ChatwootSettings,
    KnowledgeBaseSettings,
    SalesforceSettings,
    Settings,
    SlackSettings,
)


class TestSettings:
    def test_default_settings(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        settings = Settings(_env_file=None)
        assert settings.anthropic_api_key == ""
        assert isinstance(settings.salesforce, SalesforceSettings)
        assert isinstance(settings.chatwoot, ChatwootSettings)
        assert isinstance(settings.slack, SlackSettings)
        assert isinstance(settings.knowledge_base, KnowledgeBaseSettings)

    def test_salesforce_defaults(self):
        sf = SalesforceSettings(_env_file=None)
        assert sf.domain == "login"
        assert sf.username == ""

    def test_chatwoot_defaults(self):
        cw = ChatwootSettings(_env_file=None)
        assert cw.base_url == "http://localhost:3000"
        assert cw.account_id == 1

    def test_slack_defaults(self):
        slack = SlackSettings(_env_file=None)
        assert slack.escalation_channel == "#support-escalations"

    def test_knowledge_base_defaults(self):
        kb = KnowledgeBaseSettings()
        assert kb.embedding_model_name == "all-MiniLM-L6-v2"
        assert kb.knowledge_base_path == "./knowledge_base"

    def test_settings_from_env(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-123")
        settings = Settings()
        assert settings.anthropic_api_key == "sk-test-123"
