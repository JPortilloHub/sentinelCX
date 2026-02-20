"""Response accuracy evaluation against labeled tickets."""

import json
import logging
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

from sentinelcx.config import Settings
from sentinelcx.orchestrator import SentinelCXOrchestrator

logger = logging.getLogger(__name__)


async def evaluate_response_accuracy(
    settings: Settings,
    tickets_file: str = "evaluation_data/labeled_tickets.jsonl",
    sample_size: int | None = None,
) -> dict:
    """Evaluate response accuracy against labeled historical tickets.

    Runs each ticket through the pipeline and compares the generated response
    against expected keywords using semantic similarity.
    """
    tickets_path = Path(tickets_file)
    if not tickets_path.exists():
        return {"error": f"Tickets file not found: {tickets_file}"}

    # Load labeled tickets
    tickets = []
    with open(tickets_path) as f:
        for line in f:
            tickets.append(json.loads(line))

    if sample_size:
        tickets = tickets[:sample_size]

    model = SentenceTransformer(settings.knowledge_base.embedding_model_name)
    orchestrator = SentinelCXOrchestrator(settings)

    results = []
    correct = 0
    total = 0

    for ticket in tickets:
        try:
            result = await orchestrator.process_ticket(str(ticket["conversation_id"]))
            response_text = result.get("result", "")

            # Check if response contains expected keywords
            keywords = ticket.get("ideal_response_keywords", [])
            keyword_hits = sum(1 for kw in keywords if kw.lower() in response_text.lower())
            keyword_score = keyword_hits / len(keywords) if keywords else 0.0

            # Semantic similarity between response and expected keywords joined
            expected_text = " ".join(keywords)
            if response_text and expected_text:
                embeddings = model.encode([response_text, expected_text], convert_to_numpy=True)
                similarity = float(
                    np.dot(embeddings[0], embeddings[1])
                    / (np.linalg.norm(embeddings[0]) * np.linalg.norm(embeddings[1]))
                )
            else:
                similarity = 0.0

            is_correct = keyword_score >= 0.5 and similarity >= 0.3
            if is_correct:
                correct += 1
            total += 1

            results.append(
                {
                    "ticket_id": ticket["id"],
                    "category": ticket["expected_category"],
                    "keyword_score": round(keyword_score, 3),
                    "semantic_similarity": round(similarity, 3),
                    "correct": is_correct,
                }
            )
        except Exception as e:
            logger.error("Error evaluating ticket %s: %s", ticket["id"], e)
            total += 1
            results.append(
                {
                    "ticket_id": ticket["id"],
                    "error": str(e),
                    "correct": False,
                }
            )

    accuracy = correct / total if total > 0 else 0.0

    # Per-category breakdown
    category_stats = {}
    for r in results:
        cat = r.get("category", "unknown")
        if cat not in category_stats:
            category_stats[cat] = {"correct": 0, "total": 0}
        category_stats[cat]["total"] += 1
        if r.get("correct"):
            category_stats[cat]["correct"] += 1

    for cat, stats in category_stats.items():
        total = stats["total"]
        stats["accuracy"] = round(stats["correct"] / total, 3) if total > 0 else 0.0

    return {
        "overall_accuracy": round(accuracy, 3),
        "total_evaluated": total,
        "correct": correct,
        "category_breakdown": category_stats,
        "details": results,
    }
