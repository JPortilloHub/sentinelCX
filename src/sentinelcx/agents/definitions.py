"""Sub-agent definitions for the Claude Agent SDK."""

from claude_agent_sdk import AgentDefinition

from sentinelcx.agents.prompts import (
    build_escalation_prompt,
    build_research_prompt,
    build_response_prompt,
    build_triage_prompt,
)

TRIAGE_AGENT = AgentDefinition(
    description=(
        "Reads incoming tickets, extracts intent/urgency, classifies category, "
        "and decides auto-handle vs escalate. Use for every new incoming ticket."
    ),
    prompt=build_triage_prompt(),
    tools=[
        "mcp__chatwoot__get_ticket",
        "mcp__chatwoot__get_conversation_history",
        "mcp__chatwoot__get_sla_status",
        # Salesforce — check customer tier/VIP for routing decisions
        "mcp__salesforce__get_customer_record",
        "mcp__salesforce__get_account_health",
    ],
    model="sonnet",
)

RESEARCH_AGENT = AgentDefinition(
    description=(
        "Queries knowledge base and Salesforce for docs, previous resolutions, "
        "and customer context. Use when triage decides needs_research."
    ),
    prompt=build_research_prompt(),
    tools=[
        "mcp__knowledge__search_knowledge_base",
        "mcp__knowledge__get_document",
        "mcp__knowledge__list_topics",
        "mcp__salesforce__get_customer_record",
        "mcp__salesforce__get_case_history",
        "mcp__salesforce__get_purchase_history",
        "mcp__salesforce__get_account_health",
    ],
    model="sonnet",
)

RESPONSE_AGENT = AgentDefinition(
    description=(
        "Self-contained agent: reads ticket from Chatwoot, drafts reply, "
        "sends it, and marks ticket resolved. Pass ONLY the conversation_id."
    ),
    prompt=build_response_prompt(),
    tools=[
        # Read tools — Chatwoot
        "mcp__chatwoot__get_ticket",
        "mcp__chatwoot__get_conversation_history",
        # Read tools — Knowledge Base
        "mcp__knowledge__search_knowledge_base",
        "mcp__knowledge__get_document",
        # Read tools — Salesforce (customer context)
        "mcp__salesforce__get_customer_record",
        "mcp__salesforce__get_purchase_history",
        "mcp__salesforce__get_case_history",
        "mcp__salesforce__get_account_health",
        # Write tools
        "mcp__chatwoot__send_reply",
        "mcp__chatwoot__update_ticket_status",
    ],
    model="sonnet",
)

ESCALATION_AGENT = AgentDefinition(
    description=(
        "Self-contained agent: reads ticket, looks up customer in Salesforce, "
        "posts escalation to Slack, updates ticket. Pass ONLY the conversation_id."
    ),
    prompt=build_escalation_prompt(),
    tools=[
        # Read tools — Chatwoot
        "mcp__chatwoot__get_ticket",
        "mcp__chatwoot__get_conversation_history",
        # Read tools — Salesforce
        "mcp__salesforce__get_customer_record",
        "mcp__salesforce__get_account_health",
        "mcp__salesforce__get_case_history",
        # Read tools — Knowledge Base
        "mcp__knowledge__search_knowledge_base",
        "mcp__knowledge__get_document",
        # Write tools
        "mcp__slack__post_escalation",
        "mcp__chatwoot__update_ticket_status",
    ],
    model="sonnet",
)

ALL_AGENTS = {
    "triage": TRIAGE_AGENT,
    "research": RESEARCH_AGENT,
    "response": RESPONSE_AGENT,
    "escalation": ESCALATION_AGENT,
}
