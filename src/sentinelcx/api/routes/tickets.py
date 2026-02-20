"""Ticket processing endpoints."""

from fastapi import APIRouter, Request
from pydantic import BaseModel

from sentinelcx.orchestrator import SentinelCXOrchestrator

router = APIRouter()


class ProcessTicketRequest(BaseModel):
    conversation_id: str


@router.post("/tickets/process")
async def process_ticket(body: ProcessTicketRequest, request: Request) -> dict:
    """Process a support ticket through the full agent pipeline.

    Triggers triage, research, response generation, or escalation
    depending on the ticket's characteristics.
    """
    settings = request.app.state.settings
    orchestrator = SentinelCXOrchestrator(settings)
    result = await orchestrator.process_ticket(body.conversation_id)
    return result
