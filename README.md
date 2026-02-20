# sentinelCX

Enterprise Customer Support Intelligence System powered by Claude Agent SDK and Model Context Protocol (MCP).

sentinelCX orchestrates specialized AI agents to automatically triage, research, respond to, and escalate customer support tickets. It integrates with Chatwoot, Salesforce, Slack, and a semantic knowledge base to deliver intelligent, context-aware support automation.

## Architecture

```
                         +-------------------+
                         |   Chatwoot Webhook |
                         |   /webhooks/chatwoot
                         +---------+---------+
                                   |
                         +---------v---------+
                         |    Orchestrator    |
                         |  (Claude Agent SDK)|
                         +---------+---------+
                                   |
              +--------------------+--------------------+
              |                    |                     |
     +--------v-------+  +--------v-------+  +---------v--------+
     |  Triage Agent  |  | Research Agent |  | Response Agent   |
     |  (classify)    |  | (gather context)|  | (draft & send)   |
     +--------+-------+  +--------+-------+  +---------+--------+
              |                    |                     |
              |           +--------v-------+             |
              |           | Escalation Agent|            |
              |           | (Slack notify)  |            |
              |           +----------------+             |
              |                                          |
     +--------v------------------------------------------v--------+
     |                    MCP Servers (stdio)                      |
     |  Chatwoot | Salesforce | Knowledge Base | Slack             |
     +------------------------------------------------------------+
```

### Workflow

1. A ticket arrives via Chatwoot webhook or API call
2. The **Triage Agent** classifies it: `auto_handle`, `needs_research`, or `escalate`
3. Based on the decision:
   - `auto_handle` -> **Response Agent** drafts and sends a reply
   - `needs_research` -> **Research Agent** gathers context, then **Response Agent** replies
   - `escalate` -> **Escalation Agent** posts to Slack and updates the ticket

## Features

- **Multi-Agent Orchestration** -- Four specialized agents coordinated by Claude Agent SDK
- **MCP Integration** -- Chatwoot, Salesforce, Slack, and Knowledge Base exposed as MCP tool servers
- **Real-Time Dashboard** -- Live SSE-powered dashboard with metrics, agent activity, and ticket tracking
- **Semantic Knowledge Base** -- Embedding-based search over product docs, FAQs, and policies
- **Evaluation Framework** -- Accuracy, routing precision/recall, and hallucination detection
- **SQLite Persistence** -- Dashboard metrics survive server restarts
- **Webhook Support** -- Chatwoot webhooks trigger automatic ticket processing

## Quick Start

### Prerequisites

- Python 3.10+
- Anthropic API key
- Chatwoot instance (self-hosted or cloud)
- Salesforce Developer Org
- Slack workspace with bot token

### Setup

```bash
# Clone the repository
git clone https://github.com/JPortilloHub/sentinelCX.git
cd sentinelCX

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your credentials
```

### Environment Variables

```env
# Required
ANTHROPIC_API_KEY=sk-ant-...

# Chatwoot
CHATWOOT_BASE_URL=http://localhost:3000
CHATWOOT_API_TOKEN=your-token
CHATWOOT_ACCOUNT_ID=1

# Salesforce
SALESFORCE_USERNAME=user@example.com
SALESFORCE_PASSWORD=your-password
SALESFORCE_SECURITY_TOKEN=your-token
SALESFORCE_DOMAIN=login

# Slack
SLACK_BOT_TOKEN=xoxb-...
SLACK_SIGNING_SECRET=your-secret
SLACK_ESCALATION_CHANNEL=#support-escalations
```

### Seed Data

```bash
# Seed everything (Chatwoot conversations, Salesforce accounts, KB docs, eval data)
python -m seed_data.seed

# Or seed individual services
python -m seed_data.seed --chatwoot-only
python -m seed_data.seed --salesforce-only
python -m seed_data.seed --knowledge-only
python -m seed_data.seed --eval-only
```

### Run the Server

```bash
uvicorn sentinelcx.api.app:create_app --factory --reload --host 0.0.0.0 --port 8000
```

### Process a Ticket

```bash
curl -X POST http://localhost:8000/api/v1/tickets/process \
  -H "Content-Type: application/json" \
  -d '{"conversation_id": "1"}'
```

### Open the Dashboard

Navigate to http://localhost:8000/dashboard to see real-time ticket processing.

## Project Structure

```
sentinelCX/
├── src/sentinelcx/
│   ├── agents/
│   │   ├── definitions.py        # Agent configs (tools, model, prompts)
│   │   └── prompts.py            # System prompts for each agent
│   ├── api/
│   │   ├── routes/
│   │   │   ├── health.py         # GET /health
│   │   │   ├── tickets.py        # POST /api/v1/tickets/process
│   │   │   ├── evaluation.py     # POST /api/v1/evaluate/*
│   │   │   ├── dashboard.py      # GET /dashboard
│   │   │   └── dashboard_sse.py  # GET /api/v1/dashboard/events (SSE)
│   │   ├── webhooks/
│   │   │   └── chatwoot.py       # POST /webhooks/chatwoot
│   │   ├── static/
│   │   │   └── dashboard.html    # Dashboard SPA
│   │   └── app.py                # FastAPI application factory
│   ├── clients/
│   │   ├── chatwoot_client.py    # Chatwoot REST API client
│   │   ├── salesforce_client.py  # Salesforce SOQL client
│   │   └── slack_client.py       # Slack SDK wrapper
│   ├── dashboard/
│   │   ├── event_bus.py          # Pub/sub event system
│   │   ├── store.py              # SQLite persistence layer
│   │   └── log_monitor.py        # MCP log file monitor
│   ├── evaluation/
│   │   ├── accuracy.py           # Response accuracy scoring
│   │   ├── routing.py            # Routing precision/recall
│   │   └── hallucination.py      # Hallucination detection
│   ├── knowledge/
│   │   ├── indexer.py            # Embedding index builder
│   │   └── search.py            # Semantic search engine
│   ├── mcp_servers/
│   │   ├── chatwoot_server.py    # Chatwoot MCP tools
│   │   ├── salesforce_server.py  # Salesforce MCP tools
│   │   ├── knowledge_base_server.py  # KB search MCP tools
│   │   └── slack_server.py       # Slack MCP tools
│   ├── models/
│   │   ├── ticket.py             # Ticket, TriageResult, SentimentScore
│   │   ├── customer.py           # Customer, AccountHealth, CaseHistory
│   │   └── response.py           # DraftResponse, EscalationSummary
│   ├── skills/
│   │   ├── sentiment_analysis.md # Triage agent skill
│   │   ├── product_knowledge.md  # Research agent skill
│   │   └── compliance_check.md   # Response agent skill
│   ├── config.py                 # Pydantic settings
│   └── orchestrator.py           # Main orchestration logic
├── knowledge_base/
│   ├── faqs/                     # FAQ documents
│   ├── products/                 # Product documentation
│   └── policies/                 # Policy documents
├── seed_data/
│   └── seed.py                   # Data seeding CLI
├── evaluation_data/
│   ├── labeled_tickets.jsonl     # Ground truth for accuracy eval
│   └── routing_ground_truth.jsonl # Ground truth for routing eval
└── tests/
    ├── unit/
    ├── integration/
    └── e2e/
```

## Agents

### Triage Agent

Classifies incoming tickets by analyzing customer sentiment, account health, and issue type. Outputs a routing decision with confidence score.

**Tools:** Chatwoot (get ticket, conversation history, SLA status), Salesforce (customer record, account health)

**Routing rules:**
- `auto_handle` -- Clear issues with known resolutions (confidence > 0.85)
- `needs_research` -- Requires KB lookup or customer context (confidence 0.5-0.85)
- `escalate` -- Complex issues, VIP customers, high frustration, or low confidence (< 0.5)

### Research Agent

Gathers context from the knowledge base and Salesforce for tickets that need more information before responding.

**Tools:** Knowledge Base (search, get document, list topics), Salesforce (customer record, case history, purchase history, account health)

### Response Agent

Self-contained agent that reads the ticket, drafts a response using KB and customer context, sends it via Chatwoot, and marks the ticket resolved.

**Tools:** Chatwoot (get ticket, send reply, update status), Knowledge Base (search, get document), Salesforce (customer record, purchase/case history, account health)

### Escalation Agent

Posts a structured escalation summary to Slack and updates the ticket status in Chatwoot.

**Tools:** Chatwoot (get ticket, update status), Salesforce (customer record, account health, case history), Knowledge Base (search, get document), Slack (post escalation)

## MCP Servers

Each integration runs as a stdio subprocess using FastMCP:

| Server | Tools | Purpose |
|--------|-------|---------|
| **chatwoot** | `get_ticket`, `get_conversation_history`, `get_sla_status`, `send_reply`, `update_ticket_status` | Ticket management |
| **salesforce** | `get_customer_record`, `get_case_history`, `get_purchase_history`, `get_account_health` | Customer context |
| **knowledge** | `search_knowledge_base`, `get_document`, `list_topics` | Documentation search |
| **slack** | `post_escalation`, `post_message`, `check_team_availability` | Team notifications |

## Dashboard

The real-time dashboard at `/dashboard` provides:

- **Live Feed** -- Ticket processing activity with service icons showing which MCP tools are called
- **Processing Panel** -- Currently active agents and their tool calls
- **Metrics Strip** -- Decisions donut chart, category distribution, avg confidence gauge, API spend
- **History Tab** -- Browse completed tickets with drill-in detail view
- **SSE Streaming** -- Updates in real-time as tickets are processed

Dashboard state persists to SQLite (`dashboard.db`) and survives server restarts.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/tickets/process` | Process a ticket through the agent pipeline |
| `POST` | `/api/v1/evaluate/accuracy` | Evaluate response accuracy |
| `POST` | `/api/v1/evaluate/routing` | Evaluate routing precision/recall |
| `POST` | `/api/v1/evaluate/hallucination` | Detect hallucinations |
| `POST` | `/webhooks/chatwoot` | Receive Chatwoot webhook events |
| `GET` | `/dashboard` | Dashboard UI |
| `GET` | `/api/v1/dashboard/events` | SSE event stream |
| `GET` | `/api/v1/dashboard/snapshot` | Current metrics snapshot |
| `GET` | `/api/v1/dashboard/history` | Completed tickets (paginated) |
| `GET` | `/api/v1/dashboard/history/{id}` | Event timeline for a ticket |

## Evaluation

Built-in evaluation framework for measuring system quality:

- **Accuracy** -- Compares generated responses against labeled ground truth
- **Routing** -- Precision, recall, and F1 score per category
- **Hallucination** -- Detects false claims by cross-referencing KB and Salesforce data

```bash
# Run evaluations via API
curl -X POST http://localhost:8000/api/v1/evaluate/accuracy
curl -X POST http://localhost:8000/api/v1/evaluate/routing
curl -X POST http://localhost:8000/api/v1/evaluate/hallucination
```

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/

# Lint
ruff check src/ tests/

# Format
ruff format src/ tests/

# Type check
mypy src/
```

## Tech Stack

- **Claude Agent SDK** -- Agent orchestration and tool delegation
- **FastMCP** -- Model Context Protocol server framework
- **FastAPI** -- REST API and SSE streaming
- **simple-salesforce** -- Salesforce CRM integration
- **slack-sdk** -- Slack bot integration
- **sentence-transformers** -- Semantic embeddings for knowledge search
- **SQLite** -- Dashboard persistence
- **Pydantic** -- Configuration and data validation
