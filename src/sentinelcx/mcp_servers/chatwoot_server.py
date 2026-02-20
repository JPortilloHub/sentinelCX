"""Chatwoot MCP server exposing ticket and conversation tools."""

import logging

from fastmcp import FastMCP

from sentinelcx.clients.chatwoot_client import ChatwootClient
from sentinelcx.config import ChatwootSettings

_log_file = "/tmp/sentinelcx_mcp.log"
logger = logging.getLogger("mcp.chatwoot")
logger.setLevel(logging.INFO)
_fh = logging.FileHandler(_log_file)
_fh.setFormatter(logging.Formatter("%(asctime)s %(name)s %(message)s"))
logger.addHandler(_fh)

chatwoot_mcp = FastMCP("chatwoot", instructions="Chatwoot ticketing and support inbox")

_client: ChatwootClient | None = None


def init_client(settings: ChatwootSettings) -> None:
    global _client
    _client = ChatwootClient(settings)


def _get_client() -> ChatwootClient:
    if _client is None:
        raise RuntimeError("Chatwoot client not initialized. Call init_client() first.")
    return _client


@chatwoot_mcp.tool()
async def get_ticket(conversation_id: int) -> dict:
    """Fetch a support ticket/conversation by ID.

    Returns conversation details including status, assignee, contact info, and labels.
    """
    logger.info("get_ticket CALLED — conversation_id=%s", conversation_id)
    result = await _get_client().get_conversation(conversation_id)
    logger.info("get_ticket RESULT — got ticket data")
    return result


@chatwoot_mcp.tool()
async def get_conversation_history(conversation_id: int) -> list[dict]:
    """Fetch the full message history of a conversation.

    Returns all messages in chronological order with sender, content, and timestamps.
    """
    logger.info(
        "get_conversation_history CALLED — conversation_id=%s",
        conversation_id,
    )
    result = await _get_client().get_messages(conversation_id)
    logger.info(
        "get_conversation_history RESULT — %d messages",
        len(result),
    )
    return result


@chatwoot_mcp.tool()
async def get_sla_status(conversation_id: int) -> dict:
    """Get SLA compliance status for a conversation.

    Returns SLA policy details, first response due time, and current status.
    """
    return await _get_client().get_sla_status(conversation_id)


@chatwoot_mcp.tool()
async def send_reply(conversation_id: int, content: str) -> dict:
    """Send a reply message to a customer conversation.

    The message is sent as an outgoing message from the support agent.
    """
    logger.info(
        "send_reply CALLED — conversation_id=%s, content_length=%d",
        conversation_id,
        len(content),
    )
    result = await _get_client().send_message(conversation_id, content)
    logger.info("send_reply RESULT — %s", result)
    return result


@chatwoot_mcp.tool()
async def update_ticket_status(conversation_id: int, status: str) -> dict:
    """Update the status of a conversation/ticket.

    Valid statuses: open, resolved, pending, snoozed.
    """
    logger.info(
        "update_ticket_status CALLED — conversation_id=%s, status=%s",
        conversation_id,
        status,
    )
    result = await _get_client().toggle_status(conversation_id, status)
    logger.info("update_ticket_status RESULT — %s", result)
    return result


if __name__ == "__main__":
    init_client(ChatwootSettings())
    chatwoot_mcp.run()
