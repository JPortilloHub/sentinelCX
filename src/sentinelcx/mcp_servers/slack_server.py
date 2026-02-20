"""Slack MCP server exposing messaging and team availability tools."""

import logging

from fastmcp import FastMCP

from sentinelcx.clients.slack_client import SlackClient
from sentinelcx.config import SlackSettings

_log_file = "/tmp/sentinelcx_mcp.log"
logger = logging.getLogger("mcp.slack")
logger.setLevel(logging.INFO)
_fh = logging.FileHandler(_log_file)
_fh.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s"))
logger.addHandler(_fh)

slack_mcp = FastMCP("slack", instructions="Slack messaging and team collaboration")

_client: SlackClient | None = None
_escalation_channel: str = "#support-escalations"


def init_client(settings: SlackSettings) -> None:
    global _client, _escalation_channel
    _client = SlackClient(settings)
    _escalation_channel = settings.escalation_channel


def _get_client() -> SlackClient:
    if _client is None:
        raise RuntimeError("Slack client not initialized. Call init_client() first.")
    return _client


@slack_mcp.tool()
async def post_escalation(text: str) -> dict:
    """Post an escalation message to the support escalations channel.

    ALWAYS use this tool when escalating tickets. The channel is pre-configured.
    Include ticket details, customer context, priority, and recommended actions.
    """
    logger.info(
        "post_escalation CALLED — channel=%s, text_length=%d",
        _escalation_channel,
        len(text),
    )
    result = await _get_client().post_message(_escalation_channel, text)
    logger.info("post_escalation RESULT — ok=%s", result.get("ok"))
    return result


@slack_mcp.tool()
async def post_message(channel: str, text: str) -> dict:
    """Post a message to a specific Slack channel.

    Use post_escalation instead for ticket escalations.
    """
    return await _get_client().post_message(channel, text)


@slack_mcp.tool()
async def get_channel_members(channel: str) -> list[str]:
    """Get the list of member user IDs in a Slack channel.

    Returns a list of Slack user IDs for all members of the specified channel.
    """
    return await _get_client().get_channel_members(channel)


@slack_mcp.tool()
async def check_team_availability(channel: str) -> list[dict]:
    """Check the availability/presence status of team members in a channel.

    Returns a list of team members with their name, presence status, and availability.
    Useful for routing escalations to available agents.
    """
    return await _get_client().get_team_availability(channel)


@slack_mcp.tool()
async def get_user_info(user_id: str) -> dict:
    """Get detailed information about a Slack user.

    Returns user profile including name, email, title, and timezone.
    """
    return await _get_client().get_user_info(user_id)


if __name__ == "__main__":
    init_client(SlackSettings())
    slack_mcp.run()
