"""Main orchestrator that wires sub-agents and MCP servers together."""

import json as _json
import logging

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeAgentOptions,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    query,
)

from sentinelcx.agents.definitions import ALL_AGENTS
from sentinelcx.config import Settings
from sentinelcx.dashboard.event_bus import DashboardEvent, EventType, get_event_bus
from sentinelcx.mcp_servers import create_mcp_server_configs

logger = logging.getLogger(__name__)

ORCHESTRATOR_SYSTEM_PROMPT = """\
You are the sentinelCX orchestrator.

You coordinate sub-agents to process tickets.

## Workflow

1. Delegate to the **triage** agent to classify the ticket.

2. Based on triage decision:

   a) If "auto_handle": delegate to **response** agent.
   b) If "needs_research": delegate to **research** agent, \
then delegate to **response** agent.
   c) If "escalate": delegate to **escalation** agent.

3. Return the results as JSON.

## EXACT DELEGATION FORMAT

When delegating to the response agent, use EXACTLY this text \
and nothing else:
"Process conversation_id=X"

When delegating to the escalation agent, use EXACTLY this text \
and nothing else:
"Escalate conversation_id=X"

Replace X with the actual conversation ID number.

## RULES
- NEVER include ticket details, customer info, triage results, \
or any other context in delegation messages.
- The response and escalation agents are self-contained — they \
will read all data they need using their own MCP tools.
- Keep delegation messages SHORT. One line only.
"""

# Keywords to detect which sub-agent is being delegated to
_AGENT_KEYWORDS = {
    "triage": "triage",
    "research": "research",
    "response": "response",
    "escalation": "escalation",
}


class SentinelCXOrchestrator:
    """Orchestrates ticket processing through the sub-agent pipeline."""

    def __init__(self, settings: Settings | None = None) -> None:
        self._settings = settings or Settings()
        self._mcp_configs = create_mcp_server_configs()

    async def process_ticket(self, conversation_id: str) -> dict:
        """Process a support ticket through the full agent pipeline."""
        bus = get_event_bus()

        await bus.publish(
            DashboardEvent(
                type=EventType.TICKET_RECEIVED,
                conversation_id=conversation_id,
            )
        )

        prompt = (
            f"Process support ticket conversation_id={conversation_id}. "
            f"Follow the workflow: triage → route → respond or escalate. "
            f"Return the complete result as structured JSON."
        )

        def _log_stderr(line: str) -> None:
            logger.info("CLI stderr: %s", line.rstrip())

        options = ClaudeAgentOptions(
            system_prompt=ORCHESTRATOR_SYSTEM_PROMPT,
            mcp_servers=self._mcp_configs,
            agents=ALL_AGENTS,
            allowed_tools=[
                "Task",
                "mcp__chatwoot__*",
                "mcp__salesforce__*",
                "mcp__knowledge__*",
                "mcp__slack__*",
            ],
            permission_mode="bypassPermissions",
            max_turns=25,
            model="sonnet",
            stderr=_log_stderr,
            env={
                "ANTHROPIC_API_KEY": self._settings.anthropic_api_key,
                "CHATWOOT_BASE_URL": self._settings.chatwoot.base_url,
                "CHATWOOT_API_TOKEN": self._settings.chatwoot.api_token,
                "CHATWOOT_ACCOUNT_ID": str(self._settings.chatwoot.account_id),
                "SALESFORCE_USERNAME": self._settings.salesforce.username,
                "SALESFORCE_PASSWORD": self._settings.salesforce.password,
                "SALESFORCE_SECURITY_TOKEN": self._settings.salesforce.security_token,
                "SALESFORCE_DOMAIN": self._settings.salesforce.domain,
                "SLACK_BOT_TOKEN": self._settings.slack.bot_token,
                "SLACK_SIGNING_SECRET": self._settings.slack.signing_secret,
                "SLACK_ESCALATION_CHANNEL": self._settings.slack.escalation_channel,
            },
            cwd=None,
        )

        result = None
        triage_data: dict = {}

        try:
            async for message in query(prompt=prompt, options=options):
                msg_type = type(message).__name__
                logger.info(
                    "SDK message: %s (subtype=%s)",
                    msg_type,
                    getattr(message, "subtype", "N/A"),
                )

                if isinstance(message, AssistantMessage):
                    await self._emit_assistant_events(message, conversation_id, bus, triage_data)

                if isinstance(message, ResultMessage):
                    result = {
                        "success": message.subtype == "success",
                        "result": message.result,
                        "conversation_id": conversation_id,
                        "cost_usd": message.total_cost_usd,
                        "duration_ms": message.duration_ms,
                        "turns": message.num_turns,
                    }
                    logger.info(
                        "Ticket %s processed: success=%s, turns=%s, cost=$%.4f",
                        conversation_id,
                        result["success"],
                        result.get("turns"),
                        result.get("cost_usd", 0),
                    )

                    # Try to extract triage data from result if not already captured
                    if not triage_data and isinstance(message.result, str):
                        result_text = message.result
                        if '"decision"' in result_text and '"category"' in result_text:
                            try:
                                start = result_text.index("{")
                                end = result_text.rindex("}") + 1
                                parsed = _json.loads(result_text[start:end])
                                if "decision" in parsed:
                                    logger.info(
                                        "Extracted triage from result: decision=%s, category=%s",
                                        parsed.get("decision"),
                                        parsed.get("category"),
                                    )
                                    triage_data.update(parsed)
                            except (ValueError, _json.JSONDecodeError):
                                pass
        except Exception as exc:
            logger.exception("Error processing ticket %s", conversation_id)
            await bus.publish(
                DashboardEvent(
                    type=EventType.TICKET_ERROR,
                    conversation_id=conversation_id,
                    data={"error": str(exc)},
                )
            )
            if result is None:
                result = {
                    "success": False,
                    "result": str(exc),
                    "conversation_id": conversation_id,
                }

        if result is None:
            result = {
                "success": False,
                "result": "No result returned from orchestrator",
                "conversation_id": conversation_id,
            }

        await bus.publish(
            DashboardEvent(
                type=EventType.TICKET_COMPLETE,
                conversation_id=conversation_id,
                data={
                    "success": result.get("success", False),
                    "cost_usd": result.get("cost_usd", 0),
                    "duration_ms": result.get("duration_ms", 0),
                    "turns": result.get("turns", 0),
                    "decision": triage_data.get("decision", ""),
                    "category": triage_data.get("category", ""),
                    "confidence": triage_data.get("confidence"),
                },
            )
        )

        return result

    async def _emit_assistant_events(
        self,
        message: AssistantMessage,
        conversation_id: str,
        bus,
        triage_data: dict,
    ) -> None:
        """Extract dashboard events from an AssistantMessage."""
        for block in message.content:
            if isinstance(block, ToolUseBlock):
                logger.info("ToolUseBlock detected: name=%s, id=%s", block.name, block.id)

                # Detect sub-agent delegation via the Task tool
                if block.name == "Task":
                    # Try to detect agent from subagent_type parameter first
                    subagent_type = str(block.input.get("subagent_type", "")).lower()
                    if subagent_type in _AGENT_KEYWORDS:
                        agent_name = _AGENT_KEYWORDS[subagent_type]
                    else:
                        # Fall back to keyword search in description and prompt
                        desc = str(block.input.get("description", ""))
                        prompt_text = str(block.input.get("prompt", ""))
                        combined = (desc + " " + prompt_text).lower()
                        agent_name = "unknown"
                        for keyword, name in _AGENT_KEYWORDS.items():
                            if keyword in combined:
                                agent_name = name
                                break

                    logger.info(
                        "Agent delegation detected: %s (subagent_type=%s, desc=%s)",
                        agent_name,
                        subagent_type or "none",
                        block.input.get("description", "")[:50],
                    )
                    await bus.publish(
                        DashboardEvent(
                            type=EventType.AGENT_START,
                            conversation_id=conversation_id,
                            data={"agent": agent_name, "tool_use_id": block.id},
                        )
                    )
                    continue

                # Parse MCP tool name: mcp__service__tool
                parts = block.name.split("__")
                if len(parts) >= 3 and parts[0] == "mcp":
                    service = parts[1]
                    tool = "__".join(parts[2:])
                    logger.info("MCP tool call detected: service=%s, tool=%s", service, tool)
                else:
                    service = "system"
                    tool = block.name
                    logger.info("Non-MCP tool call: %s", tool)

                await bus.publish(
                    DashboardEvent(
                        type=EventType.TOOL_CALL,
                        conversation_id=conversation_id,
                        data={
                            "tool_use_id": block.id,
                            "service": service,
                            "tool": tool,
                        },
                    )
                )

            elif isinstance(block, ToolResultBlock):
                # Log the result for debugging
                result_preview = str(block.content)[:200] if block.content else ""
                logger.info(
                    "ToolResultBlock: tool_use_id=%s, is_error=%s, content_preview=%s",
                    block.tool_use_id,
                    block.is_error,
                    result_preview,
                )

                # Try to extract triage data from Task tool results
                if not triage_data and block.content:
                    content_str = str(block.content)
                    if '"decision"' in content_str and '"category"' in content_str:
                        try:
                            # Extract JSON from content (might be wrapped in text)
                            start = content_str.find("{")
                            end = content_str.rfind("}") + 1
                            if start >= 0 and end > start:
                                parsed = _json.loads(content_str[start:end])
                                if "decision" in parsed:
                                    logger.info(
                                        "Extracted triage from Task result: decision=%s, category=%s, confidence=%s",
                                        parsed.get("decision"),
                                        parsed.get("category"),
                                        parsed.get("confidence"),
                                    )
                                    triage_data.update(parsed)
                        except (ValueError, _json.JSONDecodeError) as exc:
                            logger.debug("Failed to parse JSON from Task result: %s", exc)

                await bus.publish(
                    DashboardEvent(
                        type=EventType.TOOL_RESULT,
                        conversation_id=conversation_id,
                        data={
                            "tool_use_id": block.tool_use_id,
                            "is_error": block.is_error,
                        },
                    )
                )

            elif isinstance(block, TextBlock):
                # Try to extract triage decision JSON from text
                text = block.text
                if '"decision"' in text and '"category"' in text:
                    try:
                        start = text.index("{")
                        end = text.rindex("}") + 1
                        parsed = _json.loads(text[start:end])
                        if "decision" in parsed:
                            logger.info(
                                "Extracted triage data: decision=%s, category=%s, confidence=%s",
                                parsed.get("decision"),
                                parsed.get("category"),
                                parsed.get("confidence"),
                            )
                            triage_data.update(parsed)
                    except (ValueError, _json.JSONDecodeError) as exc:
                        logger.warning("Failed to parse triage JSON: %s", exc)


async def process_ticket(conversation_id: str) -> dict:
    """Convenience function to process a ticket with default settings."""
    orchestrator = SentinelCXOrchestrator()
    return await orchestrator.process_ticket(conversation_id)
