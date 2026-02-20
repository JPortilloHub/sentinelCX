"""MCP server configuration factory for the Claude Agent SDK."""

import sys


def create_mcp_server_configs() -> dict:
    """Return MCP server configs for the Claude Agent SDK.

    Each server runs as a stdio subprocess using its FastMCP entry point.
    Environment variables are inherited from the parent process.
    """
    python = sys.executable

    return {
        "salesforce": {
            "command": python,
            "args": ["-m", "sentinelcx.mcp_servers.salesforce_server"],
        },
        "chatwoot": {
            "command": python,
            "args": ["-m", "sentinelcx.mcp_servers.chatwoot_server"],
        },
        "knowledge": {
            "command": python,
            "args": ["-m", "sentinelcx.mcp_servers.knowledge_base_server"],
        },
        "slack": {
            "command": python,
            "args": ["-m", "sentinelcx.mcp_servers.slack_server"],
        },
    }
