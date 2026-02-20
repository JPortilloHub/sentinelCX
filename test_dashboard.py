#!/usr/bin/env python3
"""Quick test to verify dashboard event system is working."""

import asyncio
from sentinelcx.dashboard.event_bus import EventType, DashboardEvent, get_event_bus


async def test_dashboard():
    """Test that events can be published and received."""
    bus = get_event_bus()

    # Publish a test event
    print("Publishing test event...")
    await bus.publish(DashboardEvent(
        type=EventType.TICKET_RECEIVED,
        conversation_id="test-123",
        data={"test": True}
    ))

    # Get snapshot
    snapshot = bus.get_snapshot()

    # Check metrics
    print(f"\nMetrics:")
    print(f"  Total processed: {snapshot['metrics']['total_processed']}")
    print(f"  Total cost: ${snapshot['metrics']['total_cost_usd']:.4f}")

    # Check recent events
    events = snapshot['recent_events']
    print(f"\nRecent events: {len(events)}")
    for event in events[-3:]:
        print(f"  - {event['type']}: conv_id={event['conversation_id']}")

    print("\n✅ Dashboard event system is working!")


if __name__ == "__main__":
    asyncio.run(test_dashboard())
