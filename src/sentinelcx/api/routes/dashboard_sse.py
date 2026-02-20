"""SSE endpoint for real-time dashboard updates."""

import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from sentinelcx.dashboard.event_bus import get_event_bus

router = APIRouter()


@router.get("/api/v1/dashboard/events")
async def dashboard_events(request: Request) -> StreamingResponse:
    """Server-Sent Events stream for live dashboard updates."""
    bus = get_event_bus()

    async def event_stream():
        queue = bus.subscribe()
        try:
            # Send initial snapshot so new clients hydrate immediately
            snapshot = bus.get_snapshot()
            yield f"event: snapshot\ndata: {json.dumps(snapshot, default=str)}\n\n"

            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    event_data = json.dumps(event.to_dict(), default=str)
                    yield f"event: {event.type.value}\ndata: {event_data}\n\n"
                except asyncio.TimeoutError:
                    # Keepalive to prevent proxy/browser timeouts
                    yield "event: ping\ndata: {}\n\n"
        finally:
            bus.unsubscribe(queue)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/api/v1/dashboard/snapshot")
async def dashboard_snapshot() -> dict:
    """REST fallback for current dashboard state."""
    return get_event_bus().get_snapshot()


@router.get("/api/v1/dashboard/history")
async def dashboard_history(limit: int = 50, offset: int = 0) -> dict:
    """Get historical completed tickets from SQLite."""
    store = get_event_bus().store
    tickets = store.get_tickets(limit=limit, offset=offset)
    return {"tickets": tickets, "limit": limit, "offset": offset}


@router.get("/api/v1/dashboard/history/{conversation_id}")
async def ticket_detail(conversation_id: str) -> dict:
    """Get all events for a specific ticket."""
    store = get_event_bus().store
    events = store.get_ticket_events(conversation_id)
    return {"conversation_id": conversation_id, "events": events}
