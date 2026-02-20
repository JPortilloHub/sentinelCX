"""Generates artificial tickets, customers, and conversations for testing."""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from seed_data.templates import CUSTOMER_NAMES, CUSTOMER_TIERS, TICKET_TEMPLATES


def _random_email(name: str) -> str:
    parts = name.lower().split()
    domains = ["example.com", "acmecorp.com", "techstart.io", "globalinc.net", "startup.co"]
    return f"{parts[0]}.{parts[1]}@{random.choice(domains)}"


def _random_date(days_back: int = 365) -> str:
    dt = datetime.utcnow() - timedelta(days=random.randint(0, days_back))
    return dt.isoformat() + "Z"


def generate_customers(count: int = 20) -> list[dict]:
    """Generate artificial customer profiles."""
    customers = []
    for i, name in enumerate(CUSTOMER_NAMES[:count]):
        customers.append(
            {
                "id": f"CUST-{i + 1:04d}",
                "account_id": f"ACC-{i + 1:04d}",
                "name": name,
                "email": _random_email(name),
                "tier": random.choice(CUSTOMER_TIERS),
                "company": f"{name.split()[1]} Inc.",
                "created_at": _random_date(730),
                "lifetime_value": round(random.uniform(500, 50000), 2),
                "total_cases": random.randint(0, 25),
            }
        )
    return customers


def generate_tickets(count: int = 200) -> list[dict]:
    """Generate labeled tickets from templates with randomization.

    Returns a list of ticket dicts with ground truth labels for evaluation.
    """
    all_templates = []
    for category, templates in TICKET_TEMPLATES.items():
        for template in templates:
            all_templates.append(template)

    customers = generate_customers()
    tickets = []

    for i in range(count):
        template = random.choice(all_templates)
        customer = random.choice(customers)
        sentiment_score = round(
            random.uniform(template["sentiment_range"][0], template["sentiment_range"][1]), 2
        )

        tickets.append(
            {
                "id": f"TICKET-{i + 1:04d}",
                "conversation_id": i + 1,
                "customer_id": customer["id"],
                "customer_name": customer["name"],
                "customer_tier": customer["tier"],
                "subject": template["subject"],
                "body": template["body"],
                "expected_category": template["expected_category"],
                "expected_priority": template["expected_priority"],
                "expected_sentiment_score": sentiment_score,
                "ideal_response_keywords": template["ideal_response_keywords"],
                "created_at": _random_date(90),
            }
        )

    return tickets


def generate_routing_ground_truth(tickets: list[dict]) -> list[dict]:
    """Generate routing ground truth from labeled tickets."""
    ground_truth = []
    for ticket in tickets:
        score = ticket["expected_sentiment_score"]
        if score > 0.8:
            expected_decision = "escalate"
        elif score < 0.3 and ticket["expected_priority"] in ("low", "medium"):
            expected_decision = "auto_handle"
        else:
            expected_decision = "needs_research"

        ground_truth.append(
            {
                "ticket_id": ticket["id"],
                "conversation_id": ticket["conversation_id"],
                "expected_category": ticket["expected_category"],
                "expected_priority": ticket["expected_priority"],
                "expected_decision": expected_decision,
            }
        )
    return ground_truth


def write_evaluation_data(output_dir: str = "evaluation_data") -> dict:
    """Generate and write evaluation datasets to JSONL files."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    tickets = generate_tickets(200)
    ground_truth = generate_routing_ground_truth(tickets)

    tickets_file = output_path / "labeled_tickets.jsonl"
    with open(tickets_file, "w") as f:
        for ticket in tickets:
            f.write(json.dumps(ticket) + "\n")

    routing_file = output_path / "routing_ground_truth.jsonl"
    with open(routing_file, "w") as f:
        for entry in ground_truth:
            f.write(json.dumps(entry) + "\n")

    return {
        "tickets_generated": len(tickets),
        "routing_entries": len(ground_truth),
        "tickets_file": str(tickets_file),
        "routing_file": str(routing_file),
    }
