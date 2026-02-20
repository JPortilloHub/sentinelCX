"""Chatwoot webhook receiver."""

import logging

from fastapi import APIRouter, BackgroundTasks, Request

from sentinelcx.orchestrator import SentinelCXOrchestrator

logger = logging.getLogger(__name__)

router = APIRouter()


async def _process_in_background(conversation_id: str, settings) -> None:
    """Process a ticket in the background after webhook receipt."""
    try:
        orchestrator = SentinelCXOrchestrator(settings)
        result = await orchestrator.process_ticket(str(conversation_id))
        logger.info(
            "Background processing complete for conversation %s: %s",
            conversation_id,
            result.get("success"),
        )
    except Exception:
        logger.exception("Error processing conversation %s", conversation_id)


@router.post("/chatwoot")
async def chatwoot_webhook(request: Request, background_tasks: BackgroundTasks) -> dict:
    """Receive Chatwoot webhook events and trigger ticket processing.

    Chatwoot sends webhooks for events like new conversations, new messages, etc.
    We filter for actionable events and process them asynchronously.
    """
    payload = await request.json()
    event_type = payload.get("event")

    # Only process new conversation or new message events
    actionable_events = {"conversation_created", "message_created"}
    if event_type not in actionable_events:
        return {"status": "ignored", "event": event_type}

    conversation_id = None
    if event_type == "conversation_created":
        conversation_id = payload.get("id")
    elif event_type == "message_created":
        conversation = payload.get("conversation", {})
        conversation_id = conversation.get("id")
        # Only process incoming messages (from customers)
        message_type = payload.get("message_type")
        if message_type != "incoming":
            return {"status": "ignored", "reason": "outgoing message"}

    if conversation_id is None:
        return {"status": "error", "reason": "no conversation_id found"}

    settings = request.app.state.settings
    background_tasks.add_task(_process_in_background, str(conversation_id), settings)

    return {"status": "accepted", "conversation_id": conversation_id}
