"""Human-in-the-loop review sample selection."""

import json
import random
from datetime import datetime
from pathlib import Path


def select_review_sample(
    processed_results: list[dict],
    sample_rate: float = 0.10,
    output_file: str | None = None,
) -> dict:
    """Select a random sample of processed tickets for human review.

    Args:
        processed_results: List of dicts with ticket processing results.
        sample_rate: Fraction of results to sample (default 10%).
        output_file: Optional path to write the review queue JSON.

    Returns:
        Dict with sample metadata and the review queue.
    """
    sample_size = max(1, int(len(processed_results) * sample_rate))
    sample = random.sample(processed_results, min(sample_size, len(processed_results)))

    review_queue = []
    for result in sample:
        review_queue.append(
            {
                "ticket_id": result.get("conversation_id", result.get("ticket_id", "")),
                "result": result.get("result", ""),
                "success": result.get("success", False),
                "cost_usd": result.get("cost_usd"),
                "review_status": "pending",
                "reviewer_notes": "",
                "rating": None,  # To be filled by reviewer: 1-5
            }
        )

    output = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_processed": len(processed_results),
        "sample_size": len(review_queue),
        "sample_rate": sample_rate,
        "review_queue": review_queue,
    }

    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(output, f, indent=2)

    return output
