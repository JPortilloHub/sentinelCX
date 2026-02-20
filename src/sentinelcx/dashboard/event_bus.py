"""In-memory event bus for dashboard real-time updates, backed by SQLite."""

import asyncio
import time
from collections import deque
from dataclasses import asdict, dataclass, field
from enum import StrEnum

from sentinelcx.dashboard.store import DashboardStore


class EventType(StrEnum):
    TICKET_RECEIVED = "ticket_received"
    AGENT_START = "agent_start"
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TICKET_COMPLETE = "ticket_complete"
    TICKET_ERROR = "ticket_error"


@dataclass
class DashboardEvent:
    type: EventType
    conversation_id: str
    timestamp: float = field(default_factory=time.time)
    data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d["type"] = self.type.value
        return d


@dataclass
class DashboardMetrics:
    total_processed: int = 0
    auto_handle_count: int = 0
    needs_research_count: int = 0
    escalate_count: int = 0
    total_cost_usd: float = 0.0
    total_duration_ms: float = 0.0
    category_counts: dict[str, int] = field(default_factory=dict)
    confidence_sum: float = 0.0
    confidence_count: int = 0


class EventBus:
    """Singleton event bus with async pub/sub, bounded in-memory history, and SQLite persistence."""

    def __init__(self, max_history: int = 100) -> None:
        self._subscribers: list[asyncio.Queue] = []
        self._history: deque[DashboardEvent] = deque(maxlen=max_history)
        self._active_tickets: dict[str, dict] = {}
        self.metrics = DashboardMetrics()
        self._store = DashboardStore()

        # Rehydrate metrics from SQLite on startup
        stored = self._store.get_metrics()
        self.metrics = DashboardMetrics(**stored)

        # Rehydrate recent events for the in-memory feed
        for ev in self._store.get_recent_events(max_history):
            self._history.append(
                DashboardEvent(
                    type=EventType(ev["type"]),
                    conversation_id=ev["conversation_id"],
                    timestamp=ev["timestamp"],
                    data=ev["data"],
                )
            )

    async def publish(self, event: DashboardEvent) -> None:
        self._history.append(event)
        self._update_state(event)

        # Persist to SQLite
        self._store.save_event(
            event.type.value,
            event.conversation_id,
            event.timestamp,
            event.data,
        )
        if event.type == EventType.TICKET_COMPLETE:
            created_at = event.timestamp
            ticket_state = self._active_tickets.get(event.conversation_id)
            if ticket_state:
                created_at = ticket_state.get("started_at", event.timestamp)
            self._store.save_ticket(
                event.conversation_id,
                {
                    **event.data,
                    "created_at": created_at,
                },
            )

        # Broadcast to SSE subscribers
        dead: list[asyncio.Queue] = []
        for queue in self._subscribers:
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                dead.append(queue)
        for q in dead:
            self._subscribers.remove(q)

    def subscribe(self) -> asyncio.Queue:
        queue: asyncio.Queue = asyncio.Queue(maxsize=256)
        self._subscribers.append(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue) -> None:
        if queue in self._subscribers:
            self._subscribers.remove(queue)

    def get_snapshot(self) -> dict:
        return {
            "metrics": asdict(self.metrics),
            "active_tickets": self._active_tickets,
            "recent_events": [e.to_dict() for e in self._history],
        }

    @property
    def store(self) -> DashboardStore:
        return self._store

    def _update_state(self, event: DashboardEvent) -> None:
        cid = event.conversation_id

        if event.type == EventType.TICKET_RECEIVED:
            self._active_tickets[cid] = {
                "conversation_id": cid,
                "started_at": event.timestamp,
                "steps": [],
                "current_agent": None,
            }

        elif event.type == EventType.AGENT_START:
            if cid in self._active_tickets:
                self._active_tickets[cid]["current_agent"] = event.data.get("agent")

        elif event.type == EventType.TOOL_CALL:
            if cid in self._active_tickets:
                self._active_tickets[cid]["steps"].append(
                    {
                        "service": event.data.get("service"),
                        "tool": event.data.get("tool"),
                        "status": "calling",
                        "timestamp": event.timestamp,
                    }
                )

        elif event.type == EventType.TOOL_RESULT:
            if cid in self._active_tickets:
                steps = self._active_tickets[cid]["steps"]
                tool_id = event.data.get("tool_use_id")
                for step in reversed(steps):
                    if step.get("tool_use_id") == tool_id or step["status"] == "calling":
                        step["status"] = "error" if event.data.get("is_error") else "done"
                        break

        elif event.type == EventType.TICKET_COMPLETE:
            self._active_tickets.pop(cid, None)
            m = self.metrics
            m.total_processed += 1
            m.total_cost_usd += event.data.get("cost_usd", 0)
            m.total_duration_ms += event.data.get("duration_ms", 0)

            decision = event.data.get("decision", "")
            if decision == "auto_handle":
                m.auto_handle_count += 1
            elif decision == "needs_research":
                m.needs_research_count += 1
            elif decision == "escalate":
                m.escalate_count += 1

            category = event.data.get("category", "")
            if category:
                m.category_counts[category] = m.category_counts.get(category, 0) + 1

            confidence = event.data.get("confidence")
            if confidence is not None:
                m.confidence_sum += confidence
                m.confidence_count += 1

        elif event.type == EventType.TICKET_ERROR:
            self._active_tickets.pop(cid, None)


_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus
