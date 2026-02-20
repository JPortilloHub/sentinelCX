"""Configuration management using Pydantic settings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SalesforceSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SALESFORCE_", env_file=".env", extra="ignore")

    username: str = ""
    password: str = ""
    security_token: str = ""
    domain: str = "login"


class ChatwootSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CHATWOOT_", env_file=".env", extra="ignore")

    base_url: str = "http://localhost:3000"
    api_token: str = ""
    account_id: int = 1


class SlackSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="SLACK_", env_file=".env", extra="ignore")

    bot_token: str = ""
    signing_secret: str = ""
    escalation_channel: str = "#support-escalations"


class KnowledgeBaseSettings(BaseSettings):
    knowledge_base_path: str = "./knowledge_base"
    embedding_model_name: str = "all-MiniLM-L6-v2"
    embedding_cache_dir: str = "./.embedding_cache"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    anthropic_api_key: str = ""
    salesforce: SalesforceSettings = Field(default_factory=SalesforceSettings)
    chatwoot: ChatwootSettings = Field(default_factory=ChatwootSettings)
    slack: SlackSettings = Field(default_factory=SlackSettings)
    knowledge_base: KnowledgeBaseSettings = Field(default_factory=KnowledgeBaseSettings)
