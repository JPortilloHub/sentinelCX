"""MCP log monitor that emits dashboard events for tool calls."""

import asyncio
import logging
import re
from pathlib import Path

from sentinelcx.dashboard.event_bus import DashboardEvent, EventType, get_event_bus

logger = logging.getLogger(__name__)

# Regex to parse MCP log lines
# Format: "2024-01-01 12:00:00,123 mcp.service get_tool_name CALLED — ..."
TOOL_CALL_PATTERN = re.compile(r"mcp\.(\w+)\s+(\w+)\s+CALLED")


class MCPLogMonitor:
    """Monitors MCP server logs and emits dashboard events."""

    def __init__(self, log_file: str = "/tmp/sentinelcx_mcp.log"):
        self.log_file = Path(log_file)
        self._running = False
        self._task = None

    async def start(self) -> None:
        """Start monitoring the MCP log file."""
        if self._running:
            return

        self._running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("MCP log monitor started: %s", self.log_file)

    async def stop(self) -> None:
        """Stop monitoring."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("MCP log monitor stopped")

    async def _monitor_loop(self) -> None:
        """Main monitoring loop that tails the log file."""
        bus = get_event_bus()
        last_position = 0
        conversation_id = "unknown"  # We'll extract this from context

        while self._running:
            try:
                # Create file if it doesn't exist
                if not self.log_file.exists():
                    self.log_file.touch()
                    await asyncio.sleep(1)
                    continue

                # Read new lines from file
                with open(self.log_file, "r") as f:
                    f.seek(last_position)
                    new_lines = f.readlines()
                    last_position = f.tell()

                # Parse and emit events
                for line in new_lines:
                    match = TOOL_CALL_PATTERN.search(line)
                    if match:
                        service = match.group(1)  # e.g. "salesforce", "knowledge"
                        tool = match.group(2)  # e.g. "get_customer_record"

                        # Try to extract conversation_id from recent context
                        # For now, use a generic ID
                        await bus.publish(
                            DashboardEvent(
                                type=EventType.TOOL_CALL,
                                conversation_id=conversation_id,
                                data={
                                    "tool_use_id": f"log_{service}_{tool}",
                                    "service": service,
                                    "tool": tool,
                                },
                            )
                        )
                        logger.debug("Emitted tool_call event: service=%s, tool=%s", service, tool)

                # Sleep before next check
                await asyncio.sleep(0.5)

            except Exception as exc:
                logger.error("Error in MCP log monitor: %s", exc)
                await asyncio.sleep(2)


# Global monitor instance
_monitor: MCPLogMonitor | None = None


def get_log_monitor() -> MCPLogMonitor:
    """Get the global log monitor instance."""
    global _monitor
    if _monitor is None:
        _monitor = MCPLogMonitor()
    return _monitor
