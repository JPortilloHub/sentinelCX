"""Event emitter for MCP servers to publish dashboard events."""

import asyncio
import logging
import time
from functools import wraps
from typing import Any, Callable

logger = logging.getLogger(__name__)


def emit_tool_call_events(service_name: str):
    """Decorator to emit dashboard events for MCP tool calls.

    This allows sub-agent tool calls to be visible in the dashboard,
    even though they happen inside Task tool executions.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            tool_name = func.__name__
            start_time = time.time()

            # Log the tool call
            logger.info(
                "MCP tool called: service=%s, tool=%s, args=%s", service_name, tool_name, kwargs
            )

            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.info(
                    "MCP tool completed: service=%s, tool=%s, duration=%.2fms",
                    service_name,
                    tool_name,
                    duration_ms,
                )
                return result
            except Exception as exc:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    "MCP tool failed: service=%s, tool=%s, error=%s, duration=%.2fms",
                    service_name,
                    tool_name,
                    str(exc),
                    duration_ms,
                )
                raise

        @wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            tool_name = func.__name__
            start_time = time.time()

            # Log the tool call
            logger.info(
                "MCP tool called: service=%s, tool=%s, args=%s", service_name, tool_name, kwargs
            )

            try:
                result = await func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                logger.info(
                    "MCP tool completed: service=%s, tool=%s, duration=%.2fms",
                    service_name,
                    tool_name,
                    duration_ms,
                )
                return result
            except Exception as exc:
                duration_ms = (time.time() - start_time) * 1000
                logger.error(
                    "MCP tool failed: service=%s, tool=%s, error=%s, duration=%.2fms",
                    service_name,
                    tool_name,
                    str(exc),
                    duration_ms,
                )
                raise

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator
